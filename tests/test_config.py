from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from bff_tools.config import (  # noqa: E402
    CONFIG_PATH_ENV,
    DATA_ROOT_ENV,
    PACKAGED_CONFIG_PATH,
    ConfigError,
    default_config_path,
    load_yaml_file,
    read_config_file,
    read_param_file,
)
from bff_tools import config as config_module  # noqa: E402


class ConfigTests(unittest.TestCase):
    def test_load_yaml_file_reads_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "config.yaml"
            path.write_text("key1: value1\nkey2: 2\n", encoding="utf-8")
            data = load_yaml_file(path)
            self.assertEqual(data["key1"], "value1")
            self.assertEqual(data["key2"], 2)

    def test_load_yaml_file_rejects_invalid_keys(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "config.yaml"
            path.write_text("badkey: value\n", encoding="utf-8")
            with self.assertRaises(ConfigError):
                load_yaml_file(path, allowed_keys=["goodkey"])

    def test_load_yaml_file_reports_io_syntax_and_shape_errors(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            with self.assertRaisesRegex(ConfigError, "Cannot read YAML"):
                load_yaml_file(tmp / "missing.yaml")

            malformed = tmp / "malformed.yaml"
            malformed.write_text("key: [unterminated\n", encoding="utf-8")
            with self.assertRaisesRegex(ConfigError, "Cannot parse YAML"):
                load_yaml_file(malformed)

            sequence = tmp / "sequence.yaml"
            sequence.write_text("- one\n- two\n", encoding="utf-8")
            with self.assertRaisesRegex(ConfigError, "Expected a mapping"):
                load_yaml_file(sequence)

    def test_read_param_file_returns_expected_keys(self) -> None:
        params = read_param_file({"mode": "vcf"})
        self.assertIn("jobid", params)
        self.assertIn("log", params)
        self.assertIn("threads", params)
        self.assertTrue(params["annotate"])
        self.assertFalse(params["jsonl"])
        self.assertEqual(params["progress_every"], 10_000)
        self.assertIsInstance(params, dict)

    def test_cli_values_override_parameter_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "params.yaml"
            path.write_text(
                "annotate: true\ngenome: hg19\ndatasetid: from-yaml\nprogress_every: 2500\n",
                encoding="utf-8",
            )
            params = read_param_file(
                {
                    "mode": "vcf",
                    "paramfile": str(path),
                    "annotate": False,
                    "genome": "hg38",
                    "datasetid": "from-cli",
                    "progress_every": 100,
                }
            )
        self.assertFalse(params["annotate"])
        self.assertEqual(params["genome"], "hg38")
        self.assertEqual(params["datasetid"], "from-cli")
        self.assertEqual(params["progress_every"], 100)

    def test_basic_vcf_config_needs_no_external_reference_bundle(self) -> None:
        with mock.patch("bff_tools.config.default_config_path", return_value=Path("/missing/config.yaml")):
            config = read_config_file(None, mode="vcf", annotate=False)
        self.assertTrue(Path(config["bash4bff"]).is_file())
        self.assertIn(
            '--progress-every "$PROGRESS_EVERY"',
            Path(config["bash4bff"]).read_text(encoding="utf-8"),
        )
        self.assertIn(
            '-dataDir "$SNPEFF_DATA" -nodownload',
            Path(config["bash4bff"]).read_text(encoding="utf-8"),
        )
        self.assertTrue(Path(config["vcf2bff"]).is_file())
        self.assertTrue(Path(config["pythonbin"]).is_file())
        self.assertNotIn("hg19fasta", config)

    def test_annotation_profile_reports_missing_configuration(self) -> None:
        with mock.patch("bff_tools.config.default_config_path", return_value=Path("/missing/config.yaml")):
            with self.assertRaisesRegex(ConfigError, "Annotation requires --config"):
                read_config_file(None, mode="vcf", annotate=True)

    def test_complete_annotation_and_tsv_profiles_are_preflighted(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            resources = {}
            for key in (
                "hg19fasta",
                "hg19clinvar",
                "hg19cosmic",
                "hg19dbnsfp",
                "snpeff",
                "snpsift",
            ):
                path = tmp / key
                path.write_text("fixture\n", encoding="utf-8")
                resources[key] = path
            config_path = tmp / "config.yaml"
            snpeff_data = tmp / "snpeff-data"
            snpeff_data.mkdir()
            config_path.write_text(
                "\n".join(
                    [
                        f"base: {tmp}",
                        "custom_path: '{base}/{arch}'",
                        "bcftools: /bin/sh",
                        "javabin: /bin/sh",
                        f"snpeffdata: {snpeff_data}",
                        f"tmpdir: {tmp}",
                        f"paneldir: {tmp}",
                        "dbnsfpset: cnag",
                    ]
                    + [f"{key}: {path}" for key, path in resources.items()]
                )
                + "\n",
                encoding="utf-8",
            )

            annotated = read_config_file(
                str(config_path),
                mode="vcf",
                annotate=True,
                genome="hg19",
                browser=True,
            )
            tsv = read_config_file(
                str(config_path),
                mode="tsv",
                annotate=False,
                genome="hg19",
            )

        self.assertIn(annotated["arch"], annotated["custom_path"])
        self.assertEqual(annotated["hs37clinvar"], annotated["hg19clinvar"])
        self.assertEqual(tsv["dbnsfpset"], "cnag")

    def test_data_root_environment_overrides_base_and_expands_home(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            home = tmp / "home"
            data_root = home / "annotation data"
            data_root.mkdir(parents=True)
            config_path = tmp / "config.yaml"
            config_path.write_text(
                "base: /ignored\nmarker: '{base}/databases'\n",
                encoding="utf-8",
            )
            with mock.patch.dict(
                "os.environ",
                {"HOME": str(home), DATA_ROOT_ENV: "~/annotation data"},
                clear=False,
            ):
                config = read_config_file(str(config_path), annotate=False)

        self.assertEqual(config["base"], str(data_root.resolve()))
        self.assertEqual(config["marker"], str(data_root.resolve() / "databases"))

    def test_data_root_reaches_every_packaged_resource_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir, mock.patch.dict(
            "os.environ",
            {CONFIG_PATH_ENV: "", DATA_ROOT_ENV: tmpdir},
            clear=False,
        ):
            config = read_config_file(None, annotate=False)

        for key in (
            "hs37fasta",
            "hg19fasta",
            "hg38fasta",
            "hg19clinvar",
            "hg38clinvar",
            "hg19cosmic",
            "hg38cosmic",
            "hg19dbnsfp",
            "hg38dbnsfp",
            "snpeffdata",
            "snpeff",
            "snpsift",
            "bcftools",
            "tmpdir",
        ):
            with self.subTest(key=key):
                self.assertTrue(config[key].startswith(str(Path(tmpdir).resolve())))
        self.assertEqual(config["javabin"], "/usr/bin/java")

    def test_missing_data_root_is_rejected_only_when_annotation_needs_it(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            missing = tmp / "missing-data"
            config_path = tmp / "config.yaml"
            config_path.write_text(
                "base: /ignored\nhg19fasta: '{base}/reference.fa.gz'\n",
                encoding="utf-8",
            )
            with mock.patch.dict(
                "os.environ",
                {DATA_ROOT_ENV: str(missing)},
                clear=False,
            ):
                basic = read_config_file(str(config_path), annotate=False)
                with self.assertRaisesRegex(ConfigError, DATA_ROOT_ENV):
                    read_config_file(str(config_path), annotate=True)

        self.assertEqual(basic["base"], str(missing.resolve()))

    def test_legacy_config_derives_snpeff_data_from_clinvar_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            snpeff_data = tmp / "snpeff" / "v5.0"
            clinvar = snpeff_data / "hg19" / "clinvar.vcf.gz"
            clinvar.parent.mkdir(parents=True)
            config_path = tmp / "config.yaml"
            config_path.write_text(
                f"hg19clinvar: {clinvar}\n",
                encoding="utf-8",
            )
            config = read_config_file(str(config_path), annotate=False)

        self.assertEqual(config["snpeffdata"], str(snpeff_data))

    def test_config_preflight_rejects_bad_values_and_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            invalid_set = tmp / "invalid-set.yaml"
            invalid_set.write_text("dbnsfpset: unsupported\n", encoding="utf-8")
            with self.assertRaisesRegex(ConfigError, "cnag.*all"):
                read_config_file(str(invalid_set), annotate=False)

            missing_panel = tmp / "missing-panel.yaml"
            missing_panel.write_text(
                f"paneldir: {tmp / 'missing'}\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ConfigError, "paneldir directory"):
                read_config_file(str(missing_panel), annotate=False, browser=True)

            with self.assertRaisesRegex(ConfigError, "required"):
                config_module._require_config_value({}, "needed", "test")
            with self.assertRaisesRegex(ConfigError, "file does not exist"):
                config_module._require_file(
                    {"file": str(tmp / "none")}, "file", "test"
                )
            with self.assertRaisesRegex(ConfigError, "executable is not available"):
                config_module._require_executable(
                    {"exe": str(tmp / "none")}, "exe", "test"
                )
            with mock.patch("bff_tools.config.shutil.which", return_value="/bin/tool"):
                config_module._require_executable({"exe": "tool"}, "exe", "test")

    def test_requested_threads_control_runtime_parameters(self) -> None:
        params = read_param_file({"mode": "vcf", "threads": 4})
        self.assertEqual(params["threads"], 4)
        self.assertEqual(params["threadsless"], 4)
        if "pigz" in params["zip"]:
            self.assertEqual(params["zip"], "/usr/bin/pigz")

    def test_jsonl_option_changes_the_genomic_variation_output(self) -> None:
        params = read_param_file({"mode": "vcf", "jsonl": True})
        self.assertTrue(params["jsonl"])
        self.assertTrue(params["gvvcfjson"].endswith("genomicVariationsVcf.jsonl.gz"))

    def test_tsv_mode_routes_input_through_tsv2vcf(self) -> None:
        params = read_param_file({"mode": "tsv", "inputfile": "cohort.tsv.gz"})
        self.assertEqual(params["pipeline"]["tsv2vcf"], 1)
        self.assertEqual(params["pipeline"]["vcf2bff"], 1)

    def test_tsv_mode_requires_annotation(self) -> None:
        with self.assertRaisesRegex(ConfigError, "annotate.*enabled"):
            read_param_file(
                {
                    "mode": "tsv",
                    "inputfile": "cohort.tsv.gz",
                    "annotate": False,
                }
            )

    def test_runtime_parameter_normalization_and_rejections(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            with mock.patch("bff_tools.config.os.cpu_count", return_value=None), mock.patch(
                "bff_tools.config.os.access", return_value=False
            ):
                params = read_param_file(
                    {
                        "mode": "vcf",
                        "genome": "b37",
                        "sampleid": "sample one",
                        "browser": True,
                    }
                )
            self.assertEqual(params["genome"], "hs37")
            self.assertEqual(params["sampleid"], "sample_one")
            self.assertEqual(params["threads"], 1)
            self.assertEqual(params["zip"], "/bin/gzip")
            self.assertEqual(params["pipeline"]["bff2html"], 1)

            existing = tmp / "existing"
            existing.mkdir()
            with self.assertRaisesRegex(ConfigError, "exists"):
                read_param_file(
                    {"mode": "vcf", "projectdir_override": str(existing)}
                )

            bad_genome = tmp / "bad-genome.yaml"
            bad_genome.write_text("genome: unknown\n", encoding="utf-8")
            with self.assertRaisesRegex(ConfigError, "valid reference genome"):
                read_param_file({"mode": "vcf", "paramfile": str(bad_genome)})

            with self.assertRaisesRegex(ConfigError, "Invalid mode"):
                read_param_file({"mode": "unknown"})

    def test_human_alias_and_new_project_override_are_normalized(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            destination = Path(tmpdir) / "new-output"
            param_file = Path(tmpdir) / "params.yaml"
            param_file.write_text("organism: human\n", encoding="utf-8")
            params = read_param_file(
                {
                    "mode": "vcf",
                    "paramfile": str(param_file),
                    "projectdir_override": str(destination),
                }
            )
        self.assertEqual(params["organism"], "Homo sapiens")
        self.assertEqual(params["projectdir"], str(destination))

    def test_default_config_path_uses_repository_default(self) -> None:
        with mock.patch.dict("os.environ", {}, clear=True):
            path = default_config_path()
        self.assertEqual(path, ROOT / "bin" / "config.yaml")

    def test_default_config_path_uses_packaged_default_outside_checkout(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir, mock.patch.object(
            config_module, "ROOT_DIR", Path(tmpdir)
        ), mock.patch.dict("os.environ", {}, clear=True):
            path = default_config_path()
        self.assertEqual(path, PACKAGED_CONFIG_PATH)
        self.assertTrue(path.is_file())

    def test_packaged_and_repository_configs_have_the_same_layout(self) -> None:
        self.assertEqual(
            load_yaml_file(ROOT / "bin" / "config.yaml"),
            load_yaml_file(PACKAGED_CONFIG_PATH),
        )

    def test_default_config_path_uses_environment_override(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "annotation.yaml"
            config_path.write_text("base: /data\n", encoding="utf-8")
            with mock.patch.dict(
                "os.environ",
                {CONFIG_PATH_ENV: str(config_path)},
                clear=False,
            ):
                path = default_config_path()
        self.assertEqual(path, config_path)

    def test_default_config_path_rejects_missing_environment_override(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "missing.yaml"
            with mock.patch.dict(
                "os.environ",
                {CONFIG_PATH_ENV: str(config_path)},
                clear=False,
            ):
                with self.assertRaisesRegex(ConfigError, CONFIG_PATH_ENV):
                    default_config_path()


if __name__ == "__main__":
    unittest.main()
