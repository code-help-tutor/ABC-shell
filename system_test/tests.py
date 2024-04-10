WeChat: cstutorcs
QQ: 749389476
Email: tutorcs@163.com
import sys
import unittest
import subprocess
import re


class TestShell(unittest.TestCase):

    SHELL_IMAGE = "abc-system-test"
    TEST_VOLUME = "abc-test-volume"
    TEST_IMAGE = "abc-test-image"
    TEST_DIR = "/test"

    @classmethod
    def eval(cls, cmdline, shell="/abc/sh"):
        volume = cls.TEST_VOLUME + ":" + cls.TEST_DIR + ":"
        args = [
            "docker",
            "run",
            "--rm",
            "-v",
            volume,
            cls.TEST_IMAGE,
            shell,
            "-c",
            cmdline,
        ]
        p = subprocess.run(args, capture_output=True)
        return p.stdout.decode()

    @classmethod
    def setUpClass(cls):
        dockerfile = ("FROM " + cls.SHELL_IMAGE + "\nWORKDIR " + cls.TEST_DIR).encode()
        args = ["docker", "build", "-t", cls.TEST_IMAGE, "-"]
        p = subprocess.run(args, input=dockerfile, stdout=subprocess.DEVNULL)
        if p.returncode != 0:
            print("error: failed to build test image")
            exit(1)

    @classmethod
    def tearDownClass(cls):
        p = subprocess.run(
            ["docker", "image", "rm", cls.TEST_IMAGE], stdout=subprocess.DEVNULL
        )
        if p.returncode != 0:
            print("error: failed to remove test image")
            exit(1)

    def setUp(self):
        p = subprocess.run(
            ["docker", "volume", "create", self.TEST_VOLUME], stdout=subprocess.DEVNULL
        )
        if p.returncode != 0:
            print("error: failed to create test volume")
            exit(1)
        filesystem_setup = ";".join(
            [
                "echo \"''\" > test.txt",
                "mkdir dir1",
                "mkdir -p dir2/subdir",
                "echo AAA > dir1/file1.txt",
                "echo BBB >> dir1/file1.txt",
                "echo AAA >> dir1/file1.txt",
                "echo CCC > dir1/file2.txt",
                "for i in {1..20}; do echo $i >> dir1/longfile.txt; done",
                "echo AAA > dir2/subdir/file.txt",
                "echo aaa >> dir2/subdir/file.txt",
                "echo AAA >> dir2/subdir/file.txt",
                "touch dir1/subdir/.hidden",
            ]
        )
        self.eval(filesystem_setup, shell="/bin/bash")

    def tearDown(self):
        p = subprocess.run(
            ["docker", "volume", "rm", self.TEST_VOLUME], stdout=subprocess.DEVNULL
        )
        if p.returncode != 0:
            print("error: failed to remove test volume")
            exit(1)

    def test_echo(self):
        cmdline = "echo hello world"
        stdout = self.eval(cmdline)
        result = stdout.strip()
        self.assertEqual(result, "hello world")

    def test_ls(self):
        cmdline = "ls"
        stdout = self.eval(cmdline)
        result = set(re.split("\n|\t", stdout.strip()))
        self.assertEqual(result, {"test.txt", "dir1", "dir2"})

    def test_ls_dir(self):
        cmdline = "ls dir1"
        stdout = self.eval(cmdline)
        result = set(re.split("\n|\t", stdout.strip()))
        self.assertEqual(result, {"file1.txt", "file2.txt", "longfile.txt"})

    def test_ls_hidden(self):
        cmdline = "ls dir2/subdir"
        stdout = self.eval(cmdline)
        result = set(re.split("\n|\t", stdout.strip()))
        self.assertEqual(result, {"file.txt"})

    def test_pwd(self):
        cmdline = "pwd"
        stdout = self.eval(cmdline)
        result = stdout.strip()
        self.assertEqual(result, self.TEST_DIR)

    def test_cd_pwd(self):
        cmdline = "cd dir1; pwd"
        stdout = self.eval(cmdline)
        result = stdout.strip()
        self.assertEqual(result, self.TEST_DIR + "/dir1")

    def test_cat(self):
        cmdline = "cat dir1/file1.txt dir1/file2.txt"
        stdout = self.eval(cmdline)
        result = stdout.strip().split("\n")
        self.assertEqual(result, ["AAA", "BBB", "AAA", "CCC"])

    def test_cat_stdin(self):
        cmdline = "cat < dir1/file1.txt"
        stdout = self.eval(cmdline)
        result = stdout.strip().split("\n")
        self.assertEqual(result, ["AAA", "BBB", "AAA"])

    def test_head(self):
        cmdline = "head dir1/longfile.txt"
        stdout = self.eval(cmdline)
        result = stdout.strip().split("\n")
        self.assertEqual(result, [str(i) for i in range(1, 11)])

    def test_head_stdin(self):
        cmdline = "head < dir1/longfile.txt"
        stdout = self.eval(cmdline)
        result = stdout.strip().split("\n")
        self.assertEqual(result, [str(i) for i in range(1, 11)])

    def test_head_n5(self):
        cmdline = "head -n 5 dir1/longfile.txt"
        stdout = self.eval(cmdline)
        result = stdout.strip().split("\n")
        self.assertEqual(result, [str(i) for i in range(1, 6)])

    def test_head_n50(self):
        cmdline = "head -n 50 dir1/longfile.txt"
        stdout = self.eval(cmdline)
        result = stdout.strip().split("\n")
        self.assertEqual(result, [str(i) for i in range(1, 21)])

    def test_head_n0(self):
        cmdline = "head -n 0 dir1/longfile.txt"
        stdout = self.eval(cmdline)
        result = stdout.strip()
        self.assertEqual(result, "")

    def test_tail(self):
        cmdline = "tail dir1/longfile.txt"
        stdout = self.eval(cmdline)
        result = stdout.strip().split("\n")
        self.assertEqual(result, [str(i) for i in range(11, 21)])

    def test_tail_stdin(self):
        cmdline = "tail < dir1/longfile.txt"
        stdout = self.eval(cmdline)
        result = stdout.strip().split("\n")
        self.assertEqual(result, [str(i) for i in range(11, 21)])

    def test_tail_n5(self):
        cmdline = "tail -n 5 dir1/longfile.txt"
        stdout = self.eval(cmdline)
        result = stdout.strip().split("\n")
        self.assertEqual(result, [str(i) for i in range(16, 21)])

    def test_tail_n50(self):
        cmdline = "tail -n 50 dir1/longfile.txt"
        stdout = self.eval(cmdline)
        result = stdout.strip().split("\n")
        self.assertEqual(result, [str(i) for i in range(1, 21)])

    def test_tail_n0(self):
        cmdline = "tail -n 0 dir1/longfile.txt"
        stdout = self.eval(cmdline)
        result = stdout.strip()
        self.assertEqual(result, "")

    def test_grep(self):
        cmdline = "grep AAA dir1/file1.txt"
        stdout = self.eval(cmdline)
        result = stdout.strip().split("\n")
        self.assertEqual(result, ["AAA", "AAA"])

    def test_grep_no_matches(self):
        cmdline = "grep DDD dir1/file1.txt"
        stdout = self.eval(cmdline)
        result = stdout.strip()
        self.assertEqual(result, "")

    def test_grep_re(self):
        cmdline = "grep 'A..' dir1/file1.txt"
        stdout = self.eval(cmdline)
        result = stdout.strip().split("\n")
        self.assertEqual(result, ["AAA", "AAA"])

    def test_grep_files(self):
        cmdline = "grep '...' dir1/file1.txt dir1/file2.txt"
        stdout = self.eval(cmdline)
        result = stdout.strip().split("\n")
        self.assertEqual(
            result,
            [
                "dir1/file1.txt:AAA",
                "dir1/file1.txt:BBB",
                "dir1/file1.txt:AAA",
                "dir1/file2.txt:CCC",
            ],
        )

    def test_grep_stdin(self):
        cmdline = "cat dir1/file1.txt dir1/file2.txt | grep '...'"
        stdout = self.eval(cmdline)
        result = stdout.strip().split("\n")
        self.assertEqual(result, ["AAA", "BBB", "AAA", "CCC"])

    def test_sort(self):
        cmdline = "sort dir1/file1.txt"
        stdout = self.eval(cmdline)
        result = stdout.strip().split("\n")
        self.assertEqual(result, ["AAA", "AAA", "BBB"])

    def test_sort_stdin(self):
        cmdline = "sort < dir1/file1.txt"
        stdout = self.eval(cmdline)
        result = stdout.strip().split("\n")
        self.assertEqual(result, ["AAA", "AAA", "BBB"])

    def test_sort_r(self):
        cmdline = "sort -r dir1/file1.txt"
        stdout = self.eval(cmdline)
        result = stdout.strip().split("\n")
        self.assertEqual(result, ["BBB", "AAA", "AAA"])

    def test_uniq(self):
        cmdline = "uniq dir2/subdir/file.txt"
        stdout = self.eval(cmdline)
        result = stdout.strip().split("\n")
        self.assertEqual(result, ["AAA", "aaa", "AAA"])

    def test_uniq_stdin(self):
        cmdline = "uniq < dir2/subdir/file.txt"
        stdout = self.eval(cmdline)
        result = stdout.strip().split("\n")
        self.assertEqual(result, ["AAA", "aaa", "AAA"])

    def test_sort_uniq(self):
        cmdline = "sort dir1/file1.txt | uniq"
        stdout = self.eval(cmdline)
        result = stdout.strip().split("\n")
        self.assertEqual(result, ["AAA", "BBB"])

    def test_uniq_i(self):
        cmdline = "uniq -i dir2/subdir/file.txt"
        stdout = self.eval(cmdline)
        result = stdout.strip().split("\n")
        self.assertEqual(result, ["AAA"])

    def test_cut(self):
        cmdline = "cut -b 1 dir1/file1.txt"
        stdout = self.eval(cmdline)
        result = stdout.strip().split("\n")
        self.assertEqual(result, ["A", "B", "A"])

    def test_cut_interval(self):
        cmdline = "cut -b 2-3 dir1/file1.txt"
        stdout = self.eval(cmdline)
        result = stdout.strip().split("\n")
        self.assertEqual(result, ["AA", "BB", "AA"])

    def test_cut_open_interval(self):
        cmdline = "cut -b 2- dir1/file1.txt"
        stdout = self.eval(cmdline)
        result = stdout.strip().split("\n")
        self.assertEqual(result, ["AA", "BB", "AA"])

    def test_cut_overlapping(self):
        cmdline = "cut -b 2-,3- dir1/file1.txt"
        stdout = self.eval(cmdline)
        result = stdout.strip().split("\n")
        self.assertEqual(result, ["AA", "BB", "AA"])

    def test_cut_stdin(self):
        cmdline = "echo abc | cut -b 1"
        stdout = self.eval(cmdline)
        result = stdout.strip()
        self.assertEqual(result, "a")

    def test_cut_union(self):
        cmdline = "echo abc | cut -b -1,2-"
        stdout = self.eval(cmdline)
        result = stdout.strip()
        self.assertEqual(result, "abc")

    # def test_sed(self):
    #     cmdline = "sed 's/A/D/' dir1/file1.txt"
    #     stdout = self.eval(cmdline)
    #     result = stdout.strip().split("\n")
    #     self.assertEqual(result, ["DAA", "BBB", "DAA"])

    # def test_sed_stdin(self):
    #     cmdline = "sed 's/A/D/' < dir1/file1.txt"
    #     stdout = self.eval(cmdline)
    #     result = stdout.strip().split("\n")
    #     self.assertEqual(result, ["DAA", "BBB", "DAA"])

    # def test_sed_separator(self):
    #     cmdline = "sed 's|A|D|' dir1/file1.txt"
    #     stdout = self.eval(cmdline)
    #     result = stdout.strip().split("\n")
    #     self.assertEqual(result, ["DAA", "BBB", "DAA"])

    # def test_sed_g(self):
    #     cmdline = "sed 's/A/D/g' dir1/file1.txt"
    #     stdout = self.eval(cmdline)
    #     result = stdout.strip().split("\n")
    #     self.assertEqual(result, ["DDD", "BBB", "DDD"])

    # def test_sed_re(self):
    #     cmdline = "sed 's/../DD/g' dir1/file1.txt"
    #     stdout = self.eval(cmdline)
    #     result = stdout.strip().split("\n")
    #     self.assertEqual(result, ["DDA", "DDB", "DDA"])

    def test_find(self):
        cmdline = "find -name file.txt"
        stdout = self.eval(cmdline)
        result = set(re.split("\n|\t", stdout.strip()))
        self.assertEqual(result, {"./dir2/subdir/file.txt"})

    def test_find_pattern(self):
        cmdline = "find -name '*.txt'"
        stdout = self.eval(cmdline)
        result = set(re.split("\n|\t", stdout.strip()))
        self.assertEqual(
            result,
            {
                "./dir2/subdir/file.txt",
                "./test.txt",
                "./dir1/file1.txt",
                "./dir1/file2.txt",
                "./dir1/longfile.txt",
            },
        )

    def test_find_dir(self):
        cmdline = "find dir1 -name '*.txt'"
        stdout = self.eval(cmdline)
        result = set(re.split("\n|\t", stdout.strip()))
        self.assertEqual(
            result, {"dir1/file1.txt", "dir1/file2.txt", "dir1/longfile.txt"}
        )

    # def test_wc(self):
    #     cmdline = "wc dir1/file1.txt"
    #     stdout = self.eval(cmdline)
    #     result = stdout.strip().split()
    #     self.assertEqual(result, ["3", "3", "12"])

    # def test_wc_stdin(self):
    #     cmdline = "wc < dir1/file1.txt"
    #     stdout = self.eval(cmdline)
    #     result = stdout.strip().split()
    #     self.assertEqual(result, ["3", "3", "12"])

    # def test_wc_m(self):
    #     cmdline = "wc -m < dir1/file1.txt"
    #     stdout = self.eval(cmdline)
    #     result = stdout.strip()
    #     self.assertEqual(result, "12")

    # def test_wc_w(self):
    #     cmdline = "wc -w < dir1/file1.txt"
    #     stdout = self.eval(cmdline)
    #     result = stdout.strip()
    #     self.assertEqual(result, "3")

    # def test_wc_l(self):
    #     cmdline = "wc -l < dir1/file1.txt"
    #     stdout = self.eval(cmdline)
    #     result = stdout.strip()
    #     self.assertEqual(result, "3")

    # def test_wc_files(self):
    #     cmdline = "wc -l dir1/file1.txt dir1/file2.txt"
    #     stdout = self.eval(cmdline)
    #     result = stdout.strip()
    #     self.assertEqual(result, "4")

    def test_input_redirection(self):
        cmdline = "cat < dir1/file2.txt"
        stdout = self.eval(cmdline)
        result = stdout.strip()
        self.assertEqual(result, "CCC")

    def test_input_redirection_infront(self):
        cmdline = "< dir1/file2.txt cat"
        stdout = self.eval(cmdline)
        result = stdout.strip()
        self.assertEqual(result, "CCC")

    def test_input_redirection_nospace(self):
        cmdline = "cat <dir1/file2.txt"
        stdout = self.eval(cmdline)
        result = stdout.strip()
        self.assertEqual(result, "CCC")

    def test_output_redirection(self):
        cmdline = "echo foo > newfile.txt"
        self.eval(cmdline)
        stdout = self.eval("cat newfile.txt", shell="/bin/bash")
        result = stdout.strip()
        self.assertEqual(result, "foo")

    def test_output_redirection_overwrite(self):
        cmdline = "echo foo > test.txt"
        self.eval(cmdline)
        stdout = self.eval("cat test.txt", shell="/bin/bash")
        result = stdout.strip()
        self.assertEqual(result, "foo")

    def test_globbing(self):
        cmdline = "echo *.txt"
        stdout = self.eval(cmdline)
        result = set(stdout.strip().split())
        self.assertEqual(result, {"test.txt"})

    def test_globbing_dir(self):
        cmdline = "echo dir1/*.txt"
        stdout = self.eval(cmdline)
        result = set(stdout.strip().split())
        self.assertEqual(
            result, {"dir1/file1.txt", "dir1/file2.txt", "dir1/longfile.txt"}
        )

    def test_semicolon(self):
        cmdline = "echo AAA; echo BBB"
        stdout = self.eval(cmdline)
        result = set(stdout.strip().split())
        self.assertEqual(result, {"AAA", "BBB"})

    def test_semicolon_chain(self):
        cmdline = "echo AAA; echo BBB; echo CCC"
        stdout = self.eval(cmdline)
        result = set(stdout.strip().split())
        self.assertEqual(result, {"AAA", "BBB", "CCC"})

    def test_semicolon_exception(self):
        cmdline = "ls dir3; echo BBB"
        stdout = self.eval(cmdline)
        result = stdout.strip()
        self.assertEqual(result, "")

    def test_pipe_uniq(self):
        cmdline = (
            "echo aaa > dir1/file2.txt; cat dir1/file1.txt dir1/file2.txt | uniq -i"
        )
        stdout = self.eval(cmdline)
        result = stdout.strip().split("\n")
        self.assertEqual(result, ["AAA", "BBB", "AAA"])

    # def test_pipe_`sed`(self):
    #     cmdline = "echo AAA | sed 's/A/B/'"
    #     stdout = self.eval(cmdline)
    #     result = stdout.strip()
    #     self.assertEqual(result, "BAA")

    # def test_pipe_chain_sed(self):
    #     cmdline = "echo AAA | sed 's/A/C/' | sed 's/A/B/'"
    #     stdout = self.eval(cmdline)
    #     result = stdout.strip()
    #     self.assertEqual(result, "CBA")

    def test_pipe_chain_sort_uniq(self):
        cmdline = "cat dir1/file1.txt dir1/file2.txt | sort | uniq"
        stdout = self.eval(cmdline)
        result = stdout.strip().split("\n")
        self.assertEqual(result, ["AAA", "BBB", "CCC"])

    def test_singlequotes(self):
        cmdline = "echo 'a  b'"
        stdout = self.eval(cmdline)
        result = stdout.strip()
        self.assertEqual(result, "a  b")

    def test_quote_keyword(self):
        cmdline = "echo ';'"
        stdout = self.eval(cmdline)
        result = stdout.strip()
        self.assertEqual(result, ";")

    def test_doublequotes(self):
        cmdline = 'echo "a  b"'
        stdout = self.eval(cmdline)
        result = stdout.strip()
        self.assertEqual(result, "a  b")

    def test_disabled_doublequotes(self):
        cmdline = "echo '\"\"'"
        stdout = self.eval(cmdline)
        result = stdout.strip()
        self.assertEqual(result, '""')

    def test_splitting(self):
        cmdline = 'echo a"b"c'
        stdout = self.eval(cmdline)
        result = stdout.strip()
        self.assertEqual(result, "abc")


if __name__ == "__main__":
    unittest.main()
