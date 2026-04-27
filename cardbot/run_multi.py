"""Launch multiple CardBot instances over a grid of browser windows."""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

import mss


def parse_args() -> argparse.Namespace:
    """Parse CLI options for multi-instance launcher."""
    parser = argparse.ArgumentParser(description="Launch multiple cardbot.main workers")
    parser.add_argument("--instances", type=int, default=4, help="Number of bot instances to launch")
    parser.add_argument("--rows", type=int, default=2, help="Grid rows")
    parser.add_argument("--cols", type=int, default=2, help="Grid cols")
    parser.add_argument("--padding", type=int, default=0, help="Inner padding (pixels) for each tile region")
    parser.add_argument("--monitor-index", type=int, default=1, help="MSS monitor index")
    parser.add_argument("--mode", type=str, default="observe", choices=["observe", "assist", "autoplay"])
    parser.add_argument("--agent", type=str, default="heuristic", choices=["heuristic", "random"])
    parser.add_argument("--lanes", type=int, default=4, choices=[2, 3, 4])
    parser.add_argument("--target-fps", type=float, default=30.0)
    parser.add_argument("--log-fps", type=float, default=5.0)
    parser.add_argument("--max-frames", type=int, default=0)
    parser.add_argument("--status-fps", type=float, default=2.0)
    parser.add_argument("--status-dir", type=str, default="cardbot/data/runtime_status")
    parser.add_argument(
        "--vision-profile",
        type=str,
        default=None,
        help="Optional profile path. Supports {instance_id} placeholder.",
    )
    parser.add_argument(
        "--launch-delay",
        type=float,
        default=0.2,
        help="Delay (seconds) between worker starts",
    )
    parser.add_argument("--session-dir", type=str, default="cardbot/data/sessions")
    parser.add_argument("--debug-window", action="store_true", help="Open a debug window per instance")
    return parser.parse_args()


def get_monitor_bounds(monitor_index: int) -> tuple[int, int, int, int]:
    """Return monitor bounds as (left, top, width, height)."""
    with mss.mss() as sct:
        monitors = sct.monitors
        if monitor_index < 1 or monitor_index >= len(monitors):
            monitor = monitors[1]
        else:
            monitor = monitors[monitor_index]

    return (
        int(monitor["left"]),
        int(monitor["top"]),
        int(monitor["width"]),
        int(monitor["height"]),
    )


def compute_grid_regions(
    left: int,
    top: int,
    width: int,
    height: int,
    rows: int,
    cols: int,
    padding: int,
) -> list[tuple[int, int, int, int]]:
    """Split monitor rectangle into row/column tiles."""
    tile_width = max(1, width // cols)
    tile_height = max(1, height // rows)

    regions: list[tuple[int, int, int, int]] = []
    for row in range(rows):
        for col in range(cols):
            cell_left = left + col * tile_width
            cell_top = top + row * tile_height

            if col == cols - 1:
                cell_width = left + width - cell_left
            else:
                cell_width = tile_width

            if row == rows - 1:
                cell_height = top + height - cell_top
            else:
                cell_height = tile_height

            x = cell_left + padding
            y = cell_top + padding
            w = max(1, cell_width - (2 * padding))
            h = max(1, cell_height - (2 * padding))
            regions.append((x, y, w, h))

    return regions


def build_worker_command(
    instance_id: int,
    region: tuple[int, int, int, int],
    args: argparse.Namespace,
) -> list[str]:
    """Build subprocess command for one cardbot.main worker."""
    left, top, width, height = region
    cmd = [
        sys.executable,
        "-m",
        "cardbot.main",
        "--instance-id",
        str(instance_id),
        "--monitor-index",
        str(args.monitor_index),
        "--capture-left",
        str(left),
        "--capture-top",
        str(top),
        "--capture-width",
        str(width),
        "--capture-height",
        str(height),
        "--mode",
        args.mode,
        "--agent",
        args.agent,
        "--lanes",
        str(args.lanes),
        "--target-fps",
        str(args.target_fps),
        "--log-fps",
        str(args.log_fps),
        "--status-fps",
        str(args.status_fps),
        "--status-dir",
        str(args.status_dir),
        "--session-dir",
        str(Path(args.session_dir) / f"instance_{instance_id}"),
    ]

    if args.max_frames > 0:
        cmd.extend(["--max-frames", str(args.max_frames)])
    if args.vision_profile:
        profile_path = args.vision_profile.format(instance_id=instance_id)
        cmd.extend(["--vision-profile", profile_path])
    if args.debug_window:
        cmd.append("--debug-window")

    return cmd


def main() -> None:
    """Launch and supervise multiple CardBot workers."""
    args = parse_args()

    if args.instances <= 0:
        raise ValueError("--instances must be >= 1")
    if args.rows <= 0 or args.cols <= 0:
        raise ValueError("--rows and --cols must be >= 1")
    if args.instances > (args.rows * args.cols):
        raise ValueError("instances cannot exceed rows*cols")

    mon_left, mon_top, mon_width, mon_height = get_monitor_bounds(args.monitor_index)
    regions = compute_grid_regions(
        left=mon_left,
        top=mon_top,
        width=mon_width,
        height=mon_height,
        rows=args.rows,
        cols=args.cols,
        padding=max(0, args.padding),
    )[: args.instances]

    workers: list[subprocess.Popen] = []
    failed = False
    try:
        for instance_id, region in enumerate(regions):
            cmd = build_worker_command(instance_id=instance_id, region=region, args=args)
            print(f"[MULTI] launch instance={instance_id} region={region}")
            workers.append(subprocess.Popen(cmd))
            if args.launch_delay > 0:
                time.sleep(args.launch_delay)

        while True:
            exit_codes = [worker.poll() for worker in workers]
            for idx, code in enumerate(exit_codes):
                if code is not None and code != 0:
                    print(f"[MULTI] worker {idx} exited with code {code}, terminating others")
                    failed = True
                    raise RuntimeError(f"worker {idx} failed")
            if all(code is not None for code in exit_codes):
                break
            time.sleep(0.5)

    except KeyboardInterrupt:
        print("[MULTI] stopping workers...")
        for worker in workers:
            if worker.poll() is None:
                worker.terminate()
    except RuntimeError as exc:
        print(f"[MULTI] {exc}")
        for worker in workers:
            if worker.poll() is None:
                worker.terminate()

    finally:
        for worker in workers:
            if worker.poll() is None:
                try:
                    worker.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    worker.kill()
                    worker.wait(timeout=5)

    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
