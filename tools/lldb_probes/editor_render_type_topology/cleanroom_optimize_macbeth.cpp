#include <ceres/ceres.h>

#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <vector>

namespace {

struct Vec3f {
  float v[3];
};

template <typename T>
T lab_f(const T& value) {
  return value > T(0.008856451679035631)
             ? pow(value, T(1.0 / 3.0))
             : T(7.787037037037037) * value + T(0.13793103448275862);
}

template <typename T>
void xyz_to_lab(const T xyz[3], T lab[3]) {
  union FloatWord {
    uint32_t word;
    float value;
  };
  const FloatWord white_x_word = {0x3eb0fb8d};
  const FloatWord white_y_word = {0x3eb78cd0};
  const float white_x = white_x_word.value;
  const float white_y = white_y_word.value;
  const float reciprocal_y = 1.0f / white_y;
  const float reciprocal_xn = 1.0f / (white_x * reciprocal_y);
  const float reciprocal_zn =
      1.0f / (((1.0f - white_y) - white_x) * reciprocal_y);
  const T fx = lab_f(xyz[0] * T(reciprocal_xn));
  const T fy = lab_f(xyz[1]);
  const T fz = lab_f(xyz[2] * T(reciprocal_zn));
  lab[0] = T(116.0) * fy - T(16.0);
  lab[1] = T(500.0) * (fx - fy);
  lab[2] = T(200.0) * (fy - fz);
}

template <typename T>
T radians(const T& degrees) {
  return degrees * T(3.14159265358979323846264338327950288 / 180.0);
}

template <typename T>
T degrees(const T& radians_value) {
  return radians_value * T(180.0 / 3.14159265358979323846264338327950288);
}

template <typename T>
T hue_degrees(const T& a, const T& b) {
  T hue = degrees(atan2(b, a));
  if (hue < T(0.0)) hue += T(360.0);
  return hue;
}

template <typename T>
T ciede2000(const T lab1[3], const T lab2[3]) {
  const T C1 = sqrt(lab1[1] * lab1[1] + lab1[2] * lab1[2]);
  const T C2 = sqrt(lab2[1] * lab2[1] + lab2[2] * lab2[2]);
  const T Cbar = (C1 + C2) / T(2.0);
  const T Cbar7 = pow(Cbar, T(7.0));
  const T G = T(0.5) * (T(1.0) - sqrt(Cbar7 / (Cbar7 + T(6103515625.0))));
  const T a1p = (T(1.0) + G) * lab1[1];
  const T a2p = (T(1.0) + G) * lab2[1];
  const T C1p = sqrt(a1p * a1p + lab1[2] * lab1[2]);
  const T C2p = sqrt(a2p * a2p + lab2[2] * lab2[2]);
  const T h1p = hue_degrees(a1p, lab1[2]);
  const T h2p = hue_degrees(a2p, lab2[2]);

  const T dLp = lab2[0] - lab1[0];
  const T dCp = C2p - C1p;
  T dhp = h2p - h1p;
  if (C1p * C2p == T(0.0)) {
    dhp = T(0.0);
  } else if (dhp > T(180.0)) {
    dhp -= T(360.0);
  } else if (dhp < T(-180.0)) {
    dhp += T(360.0);
  }
  const T dHp = T(2.0) * sqrt(C1p * C2p) * sin(radians(dhp / T(2.0)));

  const T Lbarp = (lab1[0] + lab2[0]) / T(2.0);
  const T Cbarp = (C1p + C2p) / T(2.0);
  T hbarp;
  if (C1p * C2p == T(0.0)) {
    hbarp = h1p + h2p;
  } else if (abs(h1p - h2p) <= T(180.0)) {
    hbarp = (h1p + h2p) / T(2.0);
  } else if (h1p + h2p < T(360.0)) {
    hbarp = (h1p + h2p + T(360.0)) / T(2.0);
  } else {
    hbarp = (h1p + h2p - T(360.0)) / T(2.0);
  }

  const T shape = T(1.0) - T(0.17) * cos(radians(hbarp - T(30.0))) +
                  T(0.24) * cos(radians(T(2.0) * hbarp)) +
                  T(0.32) * cos(radians(T(3.0) * hbarp + T(6.0))) -
                  T(0.20) * cos(radians(T(4.0) * hbarp - T(63.0)));
  const T dtheta = T(30.0) * exp(-pow((hbarp - T(275.0)) / T(25.0), T(2.0)));
  const T Cbarp7 = pow(Cbarp, T(7.0));
  const T Rc = T(2.0) * sqrt(Cbarp7 / (Cbarp7 + T(6103515625.0)));
  const T Lterm = Lbarp - T(50.0);
  const T Sl = T(1.0) + T(0.015) * Lterm * Lterm /
                           sqrt(T(20.0) + Lterm * Lterm);
  const T Sc = T(1.0) + T(0.045) * Cbarp;
  const T Sh = T(1.0) + T(0.015) * Cbarp * shape;
  const T Rt = -sin(radians(T(2.0) * dtheta)) * Rc;
  const T l = dLp / Sl;
  const T c = dCp / Sc;
  const T h = dHp / Sh;
  return sqrt(l * l + c * c + h * h + Rt * c * h);
}

struct MacbethCost {
  Vec3f source[24];
  Vec3f target[24];

  template <typename T>
  bool operator()(const T* matrix, T* residuals) const {
    for (int i = 0; i < 24; ++i) {
      T xyz[3];
      for (int row = 0; row < 3; ++row) {
        xyz[row] = matrix[row] * T(source[i].v[0]) +
                   matrix[3 + row] * T(source[i].v[1]) +
                   matrix[6 + row] * T(source[i].v[2]);
      }
      T predicted[3];
      xyz_to_lab(xyz, predicted);
      const T expected[3] = {T(target[i].v[0]), T(target[i].v[1]),
                             T(target[i].v[2])};
      residuals[i] = ciede2000(predicted, expected);
    }
    residuals[24] = T(0.0);
    return true;
  }
};

bool read_patches(const char* path, Vec3f patches[24]) {
  std::ifstream input(path, std::ios::binary);
  input.read(reinterpret_cast<char*>(patches), sizeof(Vec3f) * 24);
  return input.good() || input.gcount() == static_cast<std::streamsize>(sizeof(Vec3f) * 24);
}

void invert3(const double a[9], double inverse[9]) {
  const double determinant =
      a[0] * (a[4] * a[8] - a[5] * a[7]) -
      a[1] * (a[3] * a[8] - a[5] * a[6]) +
      a[2] * (a[3] * a[7] - a[4] * a[6]);
  inverse[0] = (a[4] * a[8] - a[5] * a[7]) / determinant;
  inverse[1] = (a[2] * a[7] - a[1] * a[8]) / determinant;
  inverse[2] = (a[1] * a[5] - a[2] * a[4]) / determinant;
  inverse[3] = (a[5] * a[6] - a[3] * a[8]) / determinant;
  inverse[4] = (a[0] * a[8] - a[2] * a[6]) / determinant;
  inverse[5] = (a[2] * a[3] - a[0] * a[5]) / determinant;
  inverse[6] = (a[3] * a[7] - a[4] * a[6]) / determinant;
  inverse[7] = (a[1] * a[6] - a[0] * a[7]) / determinant;
  inverse[8] = (a[0] * a[4] - a[1] * a[3]) / determinant;
}

void invert3f(const float source[9], float inverse[9]) {
  const float c00 = source[4] * source[8] - source[5] * source[7];
  const float c01 = -(source[1] * source[8] - source[2] * source[7]);
  const float c02 = source[1] * source[5] - source[2] * source[4];
  const float c10 = -(source[3] * source[8] - source[5] * source[6]);
  const float c11 = source[0] * source[8] - source[2] * source[6];
  const float c12 = -(source[0] * source[5] - source[2] * source[3]);
  const float c20 = source[3] * source[7] - source[4] * source[6];
  const float c21 = -(source[0] * source[7] - source[1] * source[6]);
  const float c22 = source[0] * source[4] - source[1] * source[3];
  const float determinant =
      (source[0] * c00 + source[1] * c10) + source[2] * c20;
  const float reciprocal = 1.0f / determinant;
  const float cofactors[9] = {c00, c01, c02, c10, c11,
                              c12, c20, c21, c22};
  for (int i = 0; i < 9; ++i) inverse[i] = cofactors[i] * reciprocal;
}

void white_normalize_matrix(const double column_major[9], float output[9]) {
  float raw[9];
  for (int row = 0; row < 3; ++row) {
    for (int col = 0; col < 3; ++col) {
      raw[row * 3 + col] = float(column_major[col * 3 + row]);
    }
  }
  float inverse[9];
  invert3f(raw, inverse);
  union FloatWord {
    uint32_t word;
    float value;
  };
  const FloatWord x_word = {0x3eb0fb8d};
  const FloatWord y_word = {0x3eb78cd0};
  const float reciprocal_y = 1.0f / y_word.value;
  const float xn = x_word.value * reciprocal_y;
  const float zn = ((1.0f - y_word.value) - x_word.value) * reciprocal_y;
  float neutral[3];
  for (int row = 0; row < 3; ++row) {
    neutral[row] = (inverse[row * 3] * xn + inverse[row * 3 + 1]) +
                   inverse[row * 3 + 2] * zn;
  }
  for (int row = 0; row < 3; ++row) {
    for (int col = 0; col < 3; ++col) {
      output[row * 3 + col] = raw[row * 3 + col] * neutral[col];
    }
  }
}

void initial_matrix(const Vec3f source[24], const Vec3f target_xyz[24],
                    double matrix[9]) {
  double xx[9] = {};
  double yx[9] = {};
  for (int i = 0; i < 24; ++i) {
    for (int row = 0; row < 3; ++row) {
      for (int col = 0; col < 3; ++col) {
        xx[row * 3 + col] += double(source[i].v[row]) * double(source[i].v[col]);
        yx[row * 3 + col] +=
            double(target_xyz[i].v[row]) * double(source[i].v[col]);
      }
    }
  }
  double xx_inverse[9];
  invert3(xx, xx_inverse);
  for (int row = 0; row < 3; ++row) {
    for (int col = 0; col < 3; ++col) {
      matrix[row * 3 + col] = 0.0;
      for (int k = 0; k < 3; ++k) {
        matrix[row * 3 + col] += yx[row * 3 + k] * xx_inverse[k * 3 + col];
      }
    }
  }
}

float normalize_source(Vec3f source[24], const Vec3f target_xyz[24]) {
  const float scale = target_xyz[18].v[1] / source[18].v[1];
  for (int i = 0; i < 24; ++i) {
    for (int lane = 0; lane < 3; ++lane) source[i].v[lane] *= scale;
  }
  return scale;
}

}  // namespace

int main(int argc, char** argv) {
  if (argc != 4) {
    std::cerr << "usage: " << argv[0]
              << " source.raw target_lab.raw target_xyz.raw\n";
    return 2;
  }
  MacbethCost cost;
  Vec3f target_xyz[24];
  if (!read_patches(argv[1], cost.source) || !read_patches(argv[2], cost.target)) {
    std::cerr << "failed to read 24 Vec3f patches\n";
    return 1;
  }
  if (!read_patches(argv[3], target_xyz)) {
    std::cerr << "failed to read 24 target XYZ patches\n";
    return 1;
  }
  const float source_scale = normalize_source(cost.source, target_xyz);
  double row_major_seed[9];
  initial_matrix(cost.source, target_xyz, row_major_seed);
  double matrix[9];
  for (int row = 0; row < 3; ++row) {
    for (int col = 0; col < 3; ++col) {
      matrix[col * 3 + row] = row_major_seed[row * 3 + col];
    }
  }
  double seed[9];
  std::memcpy(seed, matrix, sizeof(seed));
  ceres::Problem problem;
  problem.AddResidualBlock(
      new ceres::AutoDiffCostFunction<MacbethCost, 25, 9>(new MacbethCost(cost)),
      nullptr, matrix);
  ceres::Solver::Options options;
  options.logging_type = ceres::SILENT;
  options.linear_solver_type = ceres::DENSE_QR;
  options.minimizer_type = ceres::LINE_SEARCH;
  options.line_search_direction_type = ceres::BFGS;
  options.line_search_type = ceres::WOLFE;
  options.minimizer_progress_to_stdout = false;
  options.max_num_iterations = 2000;
  options.function_tolerance = 1e-10;
  options.gradient_tolerance = 1e-14;
  options.num_threads = 1;
  ceres::Solver::Summary summary;
  ceres::Solve(options, &problem, &summary);

  std::cout << std::setprecision(17);
  std::cout << "{\n  \"source_scale\": " << source_scale
            << ",\n  \"termination_type\": " << int(summary.termination_type)
            << ",\n  \"iterations\": " << summary.iterations.size()
            << ",\n  \"initial_cost\": " << summary.initial_cost
            << ",\n  \"final_cost\": " << summary.final_cost << ",\n";
  std::cout << "  \"seed_column_major\": [";
  for (int i = 0; i < 9; ++i) {
    std::cout.precision(17);
    std::cout << seed[i] << (i == 8 ? "" : ", ");
  }
  std::cout << "],\n";
  std::cout << "  \"matrix_column_major\": [";
  for (int i = 0; i < 9; ++i) {
    std::cout.precision(17);
    std::cout << matrix[i] << (i == 8 ? "" : ", ");
  }
  std::cout << "],\n  \"matrix_row_major_f32_words\": [";
  for (int i = 0; i < 9; ++i) {
    const int row = i / 3;
    const int col = i % 3;
    const float value = float(matrix[col * 3 + row]);
    uint32_t word;
    std::memcpy(&word, &value, sizeof(word));
    char buffer[16];
    std::snprintf(buffer, sizeof(buffer), "0x%08x", word);
    std::cout << '\"' << buffer << '\"' << (i == 8 ? "" : ", ");
  }
  static const double test_pairs[][6] = {
      {50.0, 2.6772, -79.7751, 50.0, 0.0, -82.7485},
      {50.0, 3.1571, -77.2803, 50.0, 0.0, -82.7485},
      {50.0, 2.8361, -74.0200, 50.0, 0.0, -82.7485},
      {50.0, -1.3802, -84.2814, 50.0, 0.0, -82.7485},
      {50.0, -1.1848, -84.8006, 50.0, 0.0, -82.7485},
      {50.0, -0.9009, -85.5211, 50.0, 0.0, -82.7485},
      {50.0, 0.0, 0.0, 50.0, -1.0, 2.0},
      {50.0, 2.49, -0.001, 50.0, -2.49, 0.001},
  };
  float wrapper_matrix[9];
  white_normalize_matrix(matrix, wrapper_matrix);
  std::cout << "],\n  \"wrapper_matrix_words\": [";
  for (int i = 0; i < 9; ++i) {
    uint32_t word;
    std::memcpy(&word, &wrapper_matrix[i], sizeof(word));
    char buffer[16];
    std::snprintf(buffer, sizeof(buffer), "0x%08x", word);
    std::cout << '\"' << buffer << '\"' << (i == 8 ? "" : ", ");
  }
  std::cout << "],\n  \"ciede_test_values\": [";
  for (size_t i = 0; i < sizeof(test_pairs) / sizeof(test_pairs[0]); ++i) {
    std::cout << ciede2000(test_pairs[i], test_pairs[i] + 3)
              << (i + 1 == sizeof(test_pairs) / sizeof(test_pairs[0]) ? "" : ", ");
  }
  std::cout << "]\n}\n";
  return summary.IsSolutionUsable() ? 0 : 1;
}
