#!/usr/bin/env python
import logging
import os
import sys
import json
import tempfile
import subprocess as sp

from format.one_input import OneInput
from format.multi import Multi


logger = logging.getLogger(__file__)
mutate_exec = os.path.join(os.getcwd(), "run-ammon.sh")
valid_mutation = {0, 1, 3, 4, 5}
clang_style = "{BasedOnStyle: llvm, MaxEmptyLinesToKeep: 1, KeepEmptyLinesAtTheStartOfBlocks: false}"
format_funcs = {"multi": Multi().transform, "one-input": OneInput().transform}


def logger_config(log_file_name: str):
    logger.setLevel(logging.DEBUG)
    # file handler
    fh = logging.FileHandler(log_file_name, mode="w")
    fh.setLevel(logging.DEBUG)
    # cmd handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    # format
    formatter = logging.Formatter(
        "Log[%(asctime)s:%(funcName)s:%(lineno)d] - %(levelname)s: %(message)s"
    )
    ch.setFormatter(formatter)
    fh.setFormatter(formatter)
    logger.addHandler(ch)
    logger.addHandler(fh)


def check_valid(result):
    """
    使用 clang++ 编译 'mutated' 中的代码, 根据需要检查语法错误
    如果语法正确或者不需要检查，返回 True; 否则返回 False
    """
    if len(result) < 5:
        return False

    mutated = "\n".join(result[3:-1])
    desc = result[2]

    if mutated == "":
        return False

    if "syntax" in desc:
        return True

    with tempfile.NamedTemporaryFile(delete=False, suffix=".cpp") as tmp_file:
        # 将代码写入临时文件
        tmp_file.write(mutated.encode("utf-8"))
        # 获取临时文件的文件名
        tmp_filename = tmp_file.name

    # 构建 clang++ 命令来编译这个源文件
    compile_command = [
        "clang++",
        tmp_filename,
        "-c",
        "-o",
        "/dev/null",
        "-fsyntax-only",
    ]

    # 执行编译命令
    result = sp.run(compile_command, stdout=sp.PIPE, stderr=sp.PIPE, text=True)

    # 删除临时文件
    os.remove(tmp_filename)

    # 如果编译成功 (无语法错误), 返回 True
    return result.returncode == 0


def mutate(one: dict):
    problem_id = one["id"]
    logger.info("Mutation start for problem {}".format(problem_id))

    errs = []
    codes = one["answer"]
    answer_to_remove = []

    for idx, code in enumerate(codes):
        logger.info("Mutating code {}-{}".format(problem_id, idx + 1))

        with tempfile.NamedTemporaryFile(mode="w+t", delete=True, suffix=".cpp") as f:
            # write code into tempfile
            # append header file and namespace statements
            f.write("#include <bits/stdc++.h>\n")
            f.write("using namespace std;\n")
            f.write(code)
            f.write("\n")
            f.flush()

            # clang-format
            s = sp.run(
                [
                    "clang-format",
                    "-i",
                    "-style=" + clang_style,
                    f.name,
                ],
                stdout=sp.DEVNULL,
                stderr=sp.PIPE,
            )
            if s.returncode != 0:
                logger.error("Format error: {}".format(s.stderr))
                exit(1)

            # do mutatation
            cmd = [mutate_exec, f.name, "-t"]

            # 遍历所有可以使用的 mutation
            answer_mutated = []
            for t in valid_mutation:
                cur_cmd = cmd + [str(t)]
                count = 0

                # 重复某一个 mutation 最多三次, 排除偶然因素
                while True:
                    count += 1
                    logger.info(
                        "Executing '{}' for the {}-th time".format(
                            " ".join(cur_cmd), count
                        )
                    )
                    result = sp.check_output(cur_cmd, text=True).splitlines()

                    if check_valid(result):
                        info = result[1].split(" ")
                        pos = info[:2]
                        desc = result[2]
                        mutated = "\n".join(result[3:-1])

                        answer_mutated.append(
                            {"pos": pos, "code": mutated, "desc": desc}
                        )
                        break

                    logger.debug(
                        "Mutation error:\nammon result:\n{}\ncode:\n{}".format(
                            result, code
                        )
                    )

                    # 最多重复 3 次
                    if count >= 3:
                        break

            # 如果当前 answer 一个 err 都没生成
            if len(answer_mutated) == 0:
                answer_to_remove.append(idx)
            else:
                errs.append(answer_mutated)

    # 删除掉没有成功生成对应变异体的 answer
    for idx in sorted(answer_to_remove, reverse=True):
        int_idx = int(str(idx))
        logger.info("Removing invalid answer {}-{}".format(problem_id, int_idx + 1))
        codes.pop(idx)
    # append attribute error
    one["error"] = errs


def all(json_file_name: str, json_dir_name: str, transform):
    logger.info("Link start for {}".format(json_file_name))

    intermediate_file_name = os.path.join(json_dir_name, "mid.json")
    result_file_name = os.path.join(json_dir_name, "res.json")
    with open(json_file_name, "r") as f:
        # list type
        data = json.load(f)
        one_to_remove = []

        # mutate each element
        for idx, one in enumerate(data):
            mutate(one)

            # 说明一个变异体都没成功生成
            if len(one["answer"]) == 0:
                one_to_remove.append(idx)

        # 在 data 中删除无效的 one
        for idx in sorted(one_to_remove, reverse=True):
            logger.info("Removing invalid problem {}".format(data[idx]["id"]))
            data.pop(idx)

        # conversations
        convs = []
        # transform into conversation
        for one in data:
            convs.extend(transform(one))

        # write intermediate result into mid.json
        with open(intermediate_file_name, "w") as r:
            json.dump(data, r, indent=4)

        # write final result into res.json
        with open(result_file_name, "w") as r:
            json.dump(convs, r, indent=4)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        exit(1)
    json_file_name = sys.argv[1]
    json_dir_name = os.path.dirname(json_file_name)

    logger_config(os.path.join(json_dir_name, "all.log"))

    conv_format = sys.argv[2]
    all(json_file_name, json_dir_name, format_funcs[conv_format])
