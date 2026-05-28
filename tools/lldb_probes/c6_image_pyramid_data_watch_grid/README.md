# C6 ImagePyramid Data Watch Grid

Purpose: expand the representative C6/post-mutation ImagePyramid data-watch
probe from one watched range per run to a tele-focused grid.

Scope:

- Canonical bridge HDR profile only: `tools/lri_process --profile 3 --export-fmt 3 --no-auto-lris`.
- Canonical tele seeds only for this grid: `70mm` / `L16_03434` and `150mm` / `L16_02285`.
- Levels: `0..4`.
- Ranges per level: first, middle, and last `8` bytes of the level backing buffer.
- Zero hits prove only no read/write of those watched byte ranges under those runs. They do not prove whole-buffer terminality.

Run:

```bash
zsh tools/lldb_probes/c6_image_pyramid_data_watch_grid/run_grid.sh
```

Optional chunked run:

```bash
zsh tools/lldb_probes/c6_image_pyramid_data_watch_grid/run_grid.sh 70mm "0 1" "first middle"
```

The script defaults to one LLDB process at a time. If a run is interrupted or
the host crashes, treat all partial outputs from that run as not admitted
evidence until overwritten by a clean run and verified from JSON.

With the default single-process mode, render output is written to a shared HDR
sink in `runs/` so repeated probes do not create one large image file per grid
cell. JSON and log files remain per grid cell.

Ignored raw outputs belong under:

- `runs/c6_image_pyramid_data_watch_grid/`
