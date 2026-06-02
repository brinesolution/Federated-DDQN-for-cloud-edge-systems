import csv
import importlib.util
import tempfile
import unittest
from collections import Counter, defaultdict
from pathlib import Path


def load_generator():
    module_path = Path(__file__).with_name("code.py")
    spec = importlib.util.spec_from_file_location("dataset3_code", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_rows(path):
    with path.open(newline="", encoding="utf-8") as csv_file:
        return list(csv.DictReader(csv_file))


class Dataset3GeneratorTest(unittest.TestCase):
    def test_preserves_dataset2_schemas_and_counts(self):
        generator = load_generator()
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            generator.generate_dataset(
                output_dir=output_dir,
                n=1200,
                num_edges=8,
                num_cloud=4,
                num_timesteps=80,
                num_devices=200,
                seed=2026,
            )

            expected_counts = {
                "dataset_A.csv": 1200,
                "edge_nodes.csv": 8,
                "edge_state.csv": 8 * 80,
                "network_state.csv": 80,
                "cloud_nodes.csv": 4,
                "cloud_state.csv": 4 * 80,
            }
            expected_headers = {
                "dataset_A.csv": generator.TASK_COLUMNS,
                "edge_nodes.csv": generator.EDGE_NODE_COLUMNS,
                "edge_state.csv": generator.EDGE_STATE_COLUMNS,
                "network_state.csv": generator.NETWORK_COLUMNS,
                "cloud_nodes.csv": generator.CLOUD_NODE_COLUMNS,
                "cloud_state.csv": generator.CLOUD_STATE_COLUMNS,
            }

            for filename, expected_count in expected_counts.items():
                rows = read_rows(output_dir / filename)
                self.assertEqual(len(rows), expected_count, filename)
                self.assertEqual(list(rows[0].keys()), expected_headers[filename], filename)

    def test_realistic_contention_and_fault_signals_are_present(self):
        generator = load_generator()
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            generator.generate_dataset(
                output_dir=output_dir,
                n=1600,
                num_edges=10,
                num_cloud=4,
                num_timesteps=100,
                num_devices=250,
                seed=2027,
            )

            tasks = read_rows(output_dir / "dataset_A.csv")
            network = read_rows(output_dir / "network_state.csv")
            edge_state = read_rows(output_dir / "edge_state.csv")
            cloud_state = read_rows(output_dir / "cloud_state.csv")

            task_counts = Counter(int(row["arrival_time"]) for row in tasks)
            top_timesteps = {t for t, _ in task_counts.most_common(10)}
            bottom_timesteps = {t for t, _ in task_counts.most_common()[-10:]}

            edge_queue_by_time = defaultdict(list)
            for row in edge_state:
                edge_queue_by_time[int(row["timestep"])].append(float(row["edge_queue_length"]))

            top_queue = sum(sum(edge_queue_by_time[t]) / len(edge_queue_by_time[t]) for t in top_timesteps) / len(top_timesteps)
            bottom_queue = sum(sum(edge_queue_by_time[t]) / len(edge_queue_by_time[t]) for t in bottom_timesteps) / len(bottom_timesteps)
            self.assertGreater(top_queue, bottom_queue * 1.35)

            congested = [row for row in network if row["is_congestion"] == "1"]
            normal = [row for row in network if row["is_congestion"] == "0" and row["is_outage"] == "0"]
            self.assertGreater(len(congested), 0)
            self.assertGreater(len(normal), 0)
            congested_delay = sum(float(row["network_delay_ms"]) for row in congested) / len(congested)
            normal_delay = sum(float(row["network_delay_ms"]) for row in normal) / len(normal)
            self.assertGreater(congested_delay, normal_delay)

            outage = [row for row in network if row["is_outage"] == "1"]
            self.assertGreater(len(outage), 0)
            outage_snr = sum(float(row["snr_db"]) for row in outage) / len(outage)
            normal_snr = sum(float(row["snr_db"]) for row in normal) / len(normal)
            self.assertLess(outage_snr, normal_snr)

            self.assertGreater(sum(int(row["is_failed"]) for row in edge_state), 0)
            self.assertGreater(sum(int(row["is_degrading"]) for row in edge_state), 0)
            self.assertGreater(sum(int(row["is_in_maintenance"]) for row in cloud_state), 0)
            self.assertGreater(sum(int(row["had_cold_start"]) for row in cloud_state), 0)

            task_flags = {
                "is_corrupt": sum(int(row["is_corrupt"]) for row in tasks),
                "is_low_battery": sum(int(row["is_low_battery"]) for row in tasks),
                "impossible_deadline": sum(int(row["impossible_deadline"]) for row in tasks),
            }
            for flag, count in task_flags.items():
                self.assertGreater(count, 0, flag)


if __name__ == "__main__":
    unittest.main()
