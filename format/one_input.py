class OneInput:
    def transform(self, one) -> list:
        """
        将一个 one 中的每一对正确答案和错误变异组合起来, 按照一定格式生成生成对话
        """
        result = []
        description = one["description"]
        fmain = "int main() {}"

        for answer, errors in zip(one["answer"], one["error"]):
            for error in errors:

                error_code = error["code"]
                row, col = error["pos"]
                error_desc = error["desc"]

                # 注意有给 leetcode 加的保险
                conversation = {
                    "instruction": f"Given a problem description, incorrect code, the location of the error within the code, and a description of what's wrong, I need you to identify the mistake and provide the corrected code. Problem Description:\n{description}",
                    "input": f"Erroneous Code:\n{error_code}\n{fmain}\n\nError Location (row, column):\n({row}, {col})\n\nError Description:\n{error_desc}",
                    "output": f"{answer}\n{fmain}",
                }

                result.append(conversation)

        return result
