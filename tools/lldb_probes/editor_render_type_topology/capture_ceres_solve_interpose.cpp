#include <ceres/problem.h>
#include <ceres/solver.h>
#include <dlfcn.h>
#include <mach-o/dyld.h>

#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <iomanip>
#include <cstring>
#include <vector>

extern "C" void ceres_solve_original(const ceres::Solver::Options&,
                                      ceres::Problem*,
                                      ceres::Solver::Summary*)
    __asm__("__ZN5ceres5SolveERKNS_6Solver7OptionsEPNS_7ProblemEPNS0_7SummaryE");

static void capture_solve(const ceres::Solver::Options& options,
                          ceres::Problem* problem,
                          ceres::Solver::Summary* summary) {
  typedef void (*SolveFn)(const ceres::Solver::Options&, ceres::Problem*,
                          ceres::Solver::Summary*);
  static SolveFn real_solve = []() -> SolveFn {
    for (uint32_t i = 0; i < _dyld_image_count(); ++i) {
      const char* name = _dyld_get_image_name(i);
      if (name != nullptr && std::strstr(name, "/libceres.dylib") != nullptr) {
        return reinterpret_cast<SolveFn>(
            reinterpret_cast<uintptr_t>(_dyld_get_image_header(i)) + 0x104300);
      }
    }
    return nullptr;
  }();
  if (real_solve == nullptr) {
    std::fprintf(stderr, "capture_ceres_solve: real Solve not found\n");
    std::abort();
  }
  std::vector<double*> blocks;
  problem->GetParameterBlocks(&blocks);
  std::vector<double> before;
  if (blocks.size() == 1 && problem->ParameterBlockSize(blocks[0]) == 9) {
    before.assign(blocks[0], blocks[0] + 9);
  }
  real_solve(options, problem, summary);

  const char* output = std::getenv("L16_CERES_CAPTURE_OUT");
  if (output == nullptr || before.size() != 9) return;
  std::ofstream stream(output);
  stream << std::setprecision(17);
  stream << "{\n  \"options\": {\n"
         << "    \"minimizer_type\": " << int(options.minimizer_type) << ",\n"
         << "    \"line_search_direction_type\": " << int(options.line_search_direction_type) << ",\n"
         << "    \"line_search_type\": " << int(options.line_search_type) << ",\n"
         << "    \"linear_solver_type\": " << int(options.linear_solver_type) << ",\n"
         << "    \"max_num_iterations\": " << options.max_num_iterations << ",\n"
         << "    \"function_tolerance\": " << options.function_tolerance << ",\n"
         << "    \"gradient_tolerance\": " << options.gradient_tolerance << ",\n"
         << "    \"parameter_tolerance\": " << options.parameter_tolerance << ",\n"
         << "    \"num_threads\": " << options.num_threads << "\n  },\n";
  stream << "  \"before\": [";
  for (size_t i = 0; i < before.size(); ++i) {
    stream << before[i] << (i + 1 == before.size() ? "" : ", ");
  }
  stream << "],\n  \"after\": [";
  for (int i = 0; i < 9; ++i) {
    stream << blocks[0][i] << (i == 8 ? "" : ", ");
  }
  stream << "],\n  \"termination_type\": " << int(summary->termination_type)
         << ",\n  \"iterations\": " << summary->iterations.size()
         << ",\n  \"initial_cost\": " << summary->initial_cost
         << ",\n  \"final_cost\": " << summary->final_cost << "\n}\n";
}

__attribute__((used)) static struct {
  const void* replacement;
  const void* replacee;
} solve_interpose __attribute__((section("__DATA,__interpose"))) = {
    reinterpret_cast<const void*>(&capture_solve),
    reinterpret_cast<const void*>(&ceres_solve_original)};
