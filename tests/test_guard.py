"""Acceptance tests for doraemon-local-dev-guard V2.

Run: python -m unittest discover -s tests -v
Covers acceptance cases A-E (machine-level F/G/H/I/J are verified outside,
see README.md "Verification status").
"""
import os
import platform
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir, "scripts"))
import local_dev_guard as g  # noqa: E402


class A_EnvironmentRecognition(unittest.TestCase):
    """A. Win10 environment identification is correct (Windows-only host)."""

    @classmethod
    def setUpClass(cls):
        if platform.system() != "Windows":
            raise unittest.SkipTest("acceptance case A targets a Win10 host")

    def test_windows_family_detection(self):
        cwd = tempfile.gettempdir()
        env = g.audit_env((), include_git=False, cwd=cwd)
        self.assertEqual(env["os_family"], "windows")
        self.assertTrue(env["is_windows"])
        self.assertIn("10", env["os_release"])  # Win10/11 both report 10.x
        self.assertEqual(env["cwd"], cwd)
        self.assertTrue(env["cwd_writable"])

    def test_tools_probe_is_consistent_with_which(self):
        env = g.audit_env(("git", "definitely_missing_tool_xyz"),
                          include_git=False)
        self.assertEqual(env["tools"]["git"]["available"],
                         bool(shutil.which("git")))
        self.assertFalse(
            env["tools"]["definitely_missing_tool_xyz"]["available"])

    def test_anonymized_user_by_default(self):
        env = g.audit_env((), include_git=False)
        self.assertEqual(env["user"], "<user>")


class B_NewProjectPrefersDDrive(unittest.TestCase):
    """B. With a D drive, new projects go to the D drive."""

    def test_recommends_d_projects(self):
        drives = {"D": {"exists": True, "writable": True,
                        "free_bytes": 50 * 1024**3, "root": "D:\\"}}
        rec = g.recommend_path("demo", drives=drives, is_windows=True)
        self.assertEqual(rec["status"], "RECOMMEND")
        self.assertEqual(rec["path"], "D:\\Projects\\demo")
        self.assertFalse(rec["auto_fallback"])

    def test_real_run_prefers_d_when_available(self):
        drives = g.probe_drives()
        if not drives.get("D", {}).get("exists"):
            self.skipTest("machine has no D drive")
        rec = g.recommend_path("demo", drives=drives, is_windows=True)
        self.assertEqual(rec["status"], "RECOMMEND")
        self.assertTrue(rec["path"].startswith("D:\\"))


class C_ExistingProjectNeverMigrated(unittest.TestCase):
    """C. An existing C-drive project is not migrated."""

    def test_existing_path_kept_in_place(self):
        rec = g.recommend_path(
            "legacy_app", existing_project_path=r"C:\Users\example\legacy_app",
            drives={"D": {"exists": True, "writable": True,
                          "free_bytes": 50 * 1024**3, "root": "D:\\"}},
            is_windows=True)
        self.assertEqual(rec["status"], "USE_EXISTING")
        self.assertEqual(rec["path"], r"C:\Users\example\legacy_app")
        self.assertFalse(rec["auto_fallback"])

    def test_existing_path_wins_even_without_name(self):
        rec = g.recommend_path("", existing_project_path=r"C:\Users\example\proj")
        self.assertEqual(rec["status"], "USE_EXISTING")
        self.assertEqual(rec["path"], r"C:\Users\example\proj")


class D_NoDDriveHandled(unittest.TestCase):
    """D. No D drive is a BLOCKED case, never a silent C-drive fallback."""

    def test_no_d_drive_is_blocked(self):
        rec = g.recommend_path("demo", drives={}, is_windows=True)
        self.assertEqual(rec["status"], "BLOCKED")
        self.assertEqual(rec["code"], "NO_D_DRIVE")
        self.assertFalse(rec["auto_fallback"])
        self.assertTrue(rec["needs_authorization"])

    def test_d_not_writable_is_blocked(self):
        drives = {"D": {"exists": True, "writable": False,
                        "free_bytes": 50 * 1024**3, "root": "D:\\"}}
        rec = g.recommend_path("demo", drives=drives, is_windows=True)
        self.assertEqual(rec["code"], "D_NOT_WRITABLE")
        self.assertFalse(rec["auto_fallback"])

    def test_d_low_space_is_blocked(self):
        drives = {"D": {"exists": True, "writable": True,
                        "free_bytes": 10, "root": "D:\\"}}
        rec = g.recommend_path("demo", drives=drives, is_windows=True)
        self.assertEqual(rec["code"], "D_LOW_SPACE")
        self.assertFalse(rec["auto_fallback"])


class E_DirtyWorkspaceNeverOverwritten(unittest.TestCase):
    """E. Dirty workspace produces a report-only risk; no overwrite."""

    def test_dirty_workspace_risk(self):
        risks = g.detect_risks({"dirty_workspace": True})
        self.assertEqual(len(risks), 1)
        self.assertEqual(risks[0]["code"], "UNCOMMITTED_CHANGES")
        self.assertFalse(risks[0]["auto_fix_allowed"])

    def test_risks_are_report_only(self):
        risks = g.detect_risks({"dirty_workspace": True,
                                "path_conflict": True,
                                "missing_dep": ["node", "git"]})
        self.assertEqual({r["code"] for r in risks},
                         {"UNCOMMITTED_CHANGES", "PATH_CONFLICT",
                          "MISSING_DEP"})
        self.assertTrue(all(r["auto_fix_allowed"] is False for r in risks))


class G_PathSafety(unittest.TestCase):
    """G. project_name / existing_project_path security validation (V2.0.1)."""

    D = {"D": {"exists": True, "writable": True,
               "free_bytes": 50 * 1024**3, "root": "D:\\"}}

    # --- project_name: absolute / traversal / separators ---
    def test_traversal_rejected(self):
        for bad in ("..", "a/..", "a\\..", "../etc", "..\\win"):
            rec = g.recommend_path(bad, drives=self.D, is_windows=True)
            self.assertEqual(rec["status"], "INVALID", bad)

    def test_absolute_drive_rejected(self):
        for bad in ("C:\\x", "D:\\x", "C:x"):
            rec = g.recommend_path(bad, drives=self.D, is_windows=True)
            self.assertEqual(rec["status"], "INVALID", bad)

    def test_separators_rejected(self):
        for bad in ("a/b", "a\\b"):
            rec = g.recommend_path(bad, drives=self.D, is_windows=True)
            self.assertEqual(rec["status"], "INVALID", bad)

    def test_whitespace_and_dots_rejected(self):
        for bad in ("", "   ", ".", "..", "  "):
            rec = g.recommend_path(bad, drives=self.D, is_windows=True)
            self.assertEqual(rec["status"], "INVALID", repr(bad))

    # --- project_name: Windows-illegal characters & reserved names ---
    def test_windows_illegal_chars_rejected(self):
        for bad in ('a:b', 'a<b', 'a>c', 'a"d', "a/e", 'a|f', 'a?g', "a*h"):
            rec = g.recommend_path(bad, drives=self.D, is_windows=True)
            self.assertEqual(rec["status"], "INVALID", bad)

    def test_windows_reserved_names_rejected(self):
        for bad in ("CON", "NUL", "com1", "COM9", "LPT1", "aux"):
            rec = g.recommend_path(bad, drives=self.D, is_windows=True)
            self.assertEqual(rec["status"], "INVALID", bad)

    def test_valid_name_still_works(self):
        rec = g.recommend_path("my-app", drives=self.D, is_windows=True)
        self.assertEqual(rec["status"], "RECOMMEND")
        self.assertEqual(rec["path"], "D:\\Projects\\my-app")

    def test_whitespace_name_is_trimmed(self):
        rec = g.recommend_path("  myapp  ", drives=self.D, is_windows=True)
        self.assertEqual(rec["status"], "RECOMMEND")
        self.assertEqual(rec["path"], "D:\\Projects\\myapp")

    # --- existing_project_path: existence & directory-type, no false claims ---
    def test_existing_verified_directory(self):
        import tempfile
        d = g.recommend_path("", existing_project_path=tempfile.gettempdir())
        self.assertEqual(d["status"], "USE_EXISTING")
        self.assertTrue(d["existence_verified"])
        self.assertEqual(d["existence_verification"], "VERIFIED_DIRECTORY")

    def test_existing_missing_is_not_claimed_verified(self):
        d = g.recommend_path("", existing_project_path=r"C:\Users\example\gone")
        self.assertEqual(d["status"], "USE_EXISTING")
        self.assertFalse(d["existence_verified"])
        self.assertEqual(d["existence_verification"], "MISSING")
        self.assertIn("NOT verified", d["reason"])

    def test_existing_file_is_not_a_directory(self):
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False) as f:
            fname = f.name
        try:
            d = g.recommend_path("", existing_project_path=fname)
            self.assertEqual(d["status"], "USE_EXISTING")
            self.assertFalse(d["existence_verified"])
            self.assertEqual(d["existence_verification"], "NOT_A_DIRECTORY")
        finally:
            os.unlink(fname)

    def test_unchecked_existing_never_claims_verified(self):
        v = g.verify_existing(r"C:\x", checked=False)
        self.assertFalse(v["verified"])
        self.assertEqual(v["verification"], "NOT_CHECKED")


class F_ResponsibilityBoundary(unittest.TestCase):
    """F. Guard has no delivery / retry / acceptance machinery."""

    def test_no_forbidden_apis(self):
        public = {n for n in dir(g) if not n.startswith("_")}
        for forbidden in ("retry", "schedule", "accept", "run_delivery",
                          "resume_task", "fuse_break"):
            self.assertNotIn(forbidden, public)

    def test_risks_never_allow_autofix(self):
        risks = g.detect_risks({"dirty_workspace": True, "env_mismatch": True,
                                "insufficient_permission": True})
        self.assertTrue(all(not r["auto_fix_allowed"] for r in risks))


if __name__ == "__main__":
    unittest.main()
