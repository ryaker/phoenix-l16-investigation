#include <dlfcn.h>
#include <mach-o/dyld.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define LIBCP_PATH \
  "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib"

#define TEMP_TINT_TO_XY_VA 0xab160
#define XY_TO_CCT_TINT_VA 0xab2e0
#define ILLUMINANT_XY_VA 0xa9910
#define NEUTRAL_RGB_TO_XY_VA 0x350570
#define CCT_TINT_TO_NEUTRAL_RGB_VA 0x350820
#define LOCUS_TABLE_VA 0x66d410
#define LOCUS_ROWS 31

typedef float *(*temp_tint_to_xy_fn)(float *, float, float);
typedef float *(*xy_to_cct_tint_fn)(float *, const float *);
typedef void *(*illuminant_xy_fn)(void *, int);
typedef float *(*neutral_rgb_to_xy_fn)(float *, const void *, const float *);
typedef float *(*cct_tint_to_neutral_rgb_fn)(float *, const void *,
                                              const float *);

static intptr_t libcp_slide(void) {
  uint32_t count = _dyld_image_count();
  for (uint32_t index = 0; index < count; ++index) {
    const char *name = _dyld_get_image_name(index);
    if (name && strstr(name, "libcp.dylib")) {
      return _dyld_get_image_vmaddr_slide(index);
    }
  }
  fprintf(stderr, "libcp image was not loaded\n");
  exit(2);
}

static uint32_t bits(float value) {
  uint32_t result;
  memcpy(&result, &value, sizeof(result));
  return result;
}

static void print_float(const char *name, intptr_t slide, uintptr_t va) {
  float value;
  memcpy(&value, (const void *)(slide + va), sizeof(value));
  printf("constant name=%s va=0x%lx value=%.9g bits=0x%08x\n", name,
         (unsigned long)va, value, bits(value));
}

static void print_float4(const char *name, intptr_t slide, uintptr_t va) {
  float value[4];
  memcpy(value, (const void *)(slide + va), sizeof(value));
  printf("constant4 name=%s va=0x%lx", name, (unsigned long)va);
  for (int index = 0; index < 4; ++index) {
    printf(" v%d=%.9g b%d=0x%08x", index, value[index], index,
           bits(value[index]));
  }
  putchar('\n');
}

static void print_string_object(const char *label, intptr_t slide,
                                uintptr_t va) {
  const unsigned char *object = (const unsigned char *)(slide + va);
  uint64_t words[3];
  memcpy(words, object, sizeof(words));
  printf("property label=%s va=0x%lx raw=%016llx%016llx%016llx", label,
         (unsigned long)va, (unsigned long long)words[0],
         (unsigned long long)words[1], (unsigned long long)words[2]);

  if ((object[0] & 1u) == 0) {
    size_t size = object[0] >> 1;
    if (size <= 22) {
      printf(" value=%.*s\n", (int)size, (const char *)(object + 1));
      return;
    }
  } else if (words[1] <= 255 && words[2] != 0) {
    printf(" value=%.*s\n", (int)words[1], (const char *)(uintptr_t)words[2]);
    return;
  }
  printf(" value=<unrecognized-string-layout>\n");
}

static void print_xy_case(temp_tint_to_xy_fn convert, float temperature,
                          float tint) {
  float output[2] = {0.0f, 0.0f};
  convert(output, temperature, tint);
  printf("temp_tint_to_xy temp=%.9g tint=%.9g x=%.9g x_bits=0x%08x "
         "y=%.9g y_bits=0x%08x\n",
         temperature, tint, output[0], bits(output[0]), output[1],
         bits(output[1]));
}

static void print_cct_case(xy_to_cct_tint_fn convert, float x, float y) {
  float input[2] = {x, y};
  float output[2] = {0.0f, 0.0f};
  convert(output, input);
  printf("xy_to_cct_tint x=%.9g y=%.9g cct=%.9g cct_bits=0x%08x "
         "tint=%.9g tint_bits=0x%08x\n",
         x, y, output[0], bits(output[0]), output[1], bits(output[1]));
}

static int run_public_case(int argc, char **argv, intptr_t slide) {
  if (argc != 24) {
    fprintf(stderr,
            "usage: %s CCT_A CCT_D65 A00..A22 D6500..D6522 GAIN_R "
            "GAIN_G GAIN_B\n",
            argv[0]);
    return 2;
  }
  float values[23];
  for (int index = 0; index < 23; ++index) {
    char *end = NULL;
    values[index] = strtof(argv[index + 1], &end);
    if (!end || *end != '\0') {
      fprintf(stderr, "invalid float argument %d: %s\n", index + 1,
              argv[index + 1]);
      return 2;
    }
  }

  unsigned char calibration[0xf0];
  memset(calibration, 0, sizeof(calibration));
  memcpy(calibration + 0x00, values + 0, 2 * sizeof(float));
  memcpy(calibration + 0x10, values + 2, 9 * sizeof(float));
  memcpy(calibration + 0x34, values + 11, 9 * sizeof(float));

  float neutral[3];
  float maximum = 0.0f;
  for (int index = 0; index < 3; ++index) {
    neutral[index] = 1.0f / values[20 + index];
    if (neutral[index] > maximum) maximum = neutral[index];
  }
  float scale = 1.0f / maximum;
  for (int index = 0; index < 3; ++index) neutral[index] *= scale;

  neutral_rgb_to_xy_fn convert =
      (neutral_rgb_to_xy_fn)(slide + NEUTRAL_RGB_TO_XY_VA);
  xy_to_cct_tint_fn xy_to_cct_tint =
      (xy_to_cct_tint_fn)(slide + XY_TO_CCT_TINT_VA);
  temp_tint_to_xy_fn temp_tint_to_xy =
      (temp_tint_to_xy_fn)(slide + TEMP_TINT_TO_XY_VA);
  cct_tint_to_neutral_rgb_fn cct_tint_to_neutral_rgb =
      (cct_tint_to_neutral_rgb_fn)(slide + CCT_TINT_TO_NEUTRAL_RGB_VA);
  float xy[2] = {0.0f, 0.0f};
  float cct_tint[2] = {0.0f, 0.0f};
  float reconstructed[2] = {0.0f, 0.0f};
  float final_cct_tint[2] = {0.0f, 0.0f};
  const float standard_a_xy[2] = {0.4475726783275604f,
                                  0.40743985772132874f};
  const float standard_d65_xy[2] = {0.31272661685943604f,
                                    0.3290231227874756f};
  float standard_a_cct_tint[2] = {0.0f, 0.0f};
  float standard_d65_cct_tint[2] = {0.0f, 0.0f};
  float standard_a_neutral[3] = {0.0f, 0.0f, 0.0f};
  float standard_d65_neutral[3] = {0.0f, 0.0f, 0.0f};
  convert(xy, calibration, neutral);
  xy_to_cct_tint(cct_tint, xy);
  temp_tint_to_xy(reconstructed, cct_tint[0], cct_tint[1]);
  xy_to_cct_tint(final_cct_tint, reconstructed);
  xy_to_cct_tint(standard_a_cct_tint, standard_a_xy);
  xy_to_cct_tint(standard_d65_cct_tint, standard_d65_xy);
  cct_tint_to_neutral_rgb(standard_a_neutral, calibration,
                          standard_a_cct_tint);
  cct_tint_to_neutral_rgb(standard_d65_neutral, calibration,
                          standard_d65_cct_tint);
  printf("public_case neutral_r=%.9g neutral_r_bits=0x%08x "
         "neutral_g=%.9g neutral_g_bits=0x%08x neutral_b=%.9g "
         "neutral_b_bits=0x%08x x=%.9g x_bits=0x%08x y=%.9g "
         "y_bits=0x%08x cct=%.9g cct_bits=0x%08x tint=%.9g "
         "tint_bits=0x%08x reconstructed_x=%.9g "
         "reconstructed_x_bits=0x%08x reconstructed_y=%.9g "
         "reconstructed_y_bits=0x%08x final_cct=%.9g "
         "final_cct_bits=0x%08x final_tint=%.9g "
         "final_tint_bits=0x%08x standard_a_r=%.9g standard_a_r_bits=0x%08x "
         "standard_a_g=%.9g standard_a_g_bits=0x%08x standard_a_b=%.9g "
         "standard_a_b_bits=0x%08x standard_d65_r=%.9g "
         "standard_d65_r_bits=0x%08x standard_d65_g=%.9g "
         "standard_d65_g_bits=0x%08x standard_d65_b=%.9g "
         "standard_d65_b_bits=0x%08x\n",
         neutral[0], bits(neutral[0]), neutral[1], bits(neutral[1]),
         neutral[2], bits(neutral[2]), xy[0], bits(xy[0]), xy[1],
         bits(xy[1]), cct_tint[0], bits(cct_tint[0]), cct_tint[1],
         bits(cct_tint[1]), reconstructed[0], bits(reconstructed[0]),
         reconstructed[1], bits(reconstructed[1]), final_cct_tint[0],
         bits(final_cct_tint[0]), final_cct_tint[1],
         bits(final_cct_tint[1]), standard_a_neutral[0],
         bits(standard_a_neutral[0]), standard_a_neutral[1],
         bits(standard_a_neutral[1]), standard_a_neutral[2],
         bits(standard_a_neutral[2]), standard_d65_neutral[0],
         bits(standard_d65_neutral[0]), standard_d65_neutral[1],
         bits(standard_d65_neutral[1]), standard_d65_neutral[2],
         bits(standard_d65_neutral[2]));
  return 0;
}

int main(int argc, char **argv) {
  void *handle = dlopen(LIBCP_PATH, RTLD_NOW | RTLD_LOCAL);
  if (!handle) {
    fprintf(stderr, "dlopen failed: %s\n", dlerror());
    return 2;
  }
  intptr_t slide = libcp_slide();
  if (argc != 1) return run_public_case(argc, argv, slide);

  temp_tint_to_xy_fn temp_tint_to_xy =
      (temp_tint_to_xy_fn)(slide + TEMP_TINT_TO_XY_VA);
  xy_to_cct_tint_fn xy_to_cct_tint =
      (xy_to_cct_tint_fn)(slide + XY_TO_CCT_TINT_VA);
  illuminant_xy_fn illuminant_xy =
      (illuminant_xy_fn)(slide + ILLUMINANT_XY_VA);

  print_string_object("awb_parent", slide, 0x670d68);
  print_string_object("awb_type", slide, 0x670ca8);
  print_string_object("mode2_vector", slide, 0x670dc8);
  print_string_object("mode3_scalar_1", slide, 0x670d98);
  print_string_object("mode3_scalar_2", slide, 0x670db0);

  print_float("temperature_reciprocal_numerator", slide, 0x5aae64);
  print_float("tint_scale", slide, 0x5aae68);
  print_float("xy_u_numerator", slide, 0x5aae6c);
  print_float("xy_v_numerator", slide, 0x5aae70);
  print_float("tint_output_scale", slide, 0x5aae74);
  print_float("xy_denominator_x_scale", slide, 0x5a8878);
  print_float("xy_denominator_bias", slide, 0x5a887c);
  print_float4("xy_to_uv_scale", slide, 0x5aaf80);

  unsigned char illuminant[16];
  memset(illuminant, 0, sizeof(illuminant));
  illuminant_xy(illuminant, 5);
  float initial_xy[2];
  memcpy(initial_xy, illuminant, sizeof(initial_xy));
  printf("neutral_solver_initial illuminant=5 x=%.9g x_bits=0x%08x "
         "y=%.9g y_bits=0x%08x\n",
         initial_xy[0], bits(initial_xy[0]), initial_xy[1],
         bits(initial_xy[1]));

  const float *table = (const float *)(slide + LOCUS_TABLE_VA);
  for (int row = 0; row < LOCUS_ROWS; ++row) {
    const float *entry = table + row * 4;
    printf("locus row=%d reciprocal_temperature=%.9g reciprocal_bits=0x%08x "
           "u=%.9g u_bits=0x%08x v=%.9g v_bits=0x%08x "
           "slope=%.9g slope_bits=0x%08x\n",
           row, entry[0], bits(entry[0]), entry[1], bits(entry[1]), entry[2],
           bits(entry[2]), entry[3], bits(entry[3]));
  }

  print_xy_case(temp_tint_to_xy, 2855.63232421875f, 0.0f);
  print_xy_case(temp_tint_to_xy, 5000.0f, 0.0f);
  print_xy_case(temp_tint_to_xy, 6502.08203125f, 0.0f);
  print_xy_case(temp_tint_to_xy, 5000.0f, -10.0f);
  print_xy_case(temp_tint_to_xy, 5000.0f, 10.0f);
  print_xy_case(temp_tint_to_xy, 2855.63232421875f, -0.00412589172f);
  print_xy_case(temp_tint_to_xy, 6502.08154296875f, 9.76664829f);

  print_cct_case(xy_to_cct_tint, 0.34644079208374023f,
                 0.3529967963695526f);
  print_cct_case(xy_to_cct_tint, 0.34749817848205566f,
                 0.3551827073097229f);
  print_cct_case(xy_to_cct_tint, 0.34206733107566833f,
                 0.3483845591545105f);
  print_cct_case(xy_to_cct_tint, 0.3483559787273407f,
                 0.35049599409103394f);
  print_cct_case(xy_to_cct_tint, 0.4475726783275604f,
                 0.40743985772132874f);
  print_cct_case(xy_to_cct_tint, 0.31272661685943604f,
                 0.3290231227874756f);

  dlclose(handle);
  return 0;
}
