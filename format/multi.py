class Multi:
    def transform(self, one) -> list:
        """
        将一个 one 中的每一对正确答案和错误变异组合起来, 按照一定格式生成生成对话
        """
        result = []
        description = one["description"]
        fmain = "int main() {}"

        for idx, (answer, error) in enumerate(zip(one["answer"], one["error"])):
            error_code = error["code"]
            row, col = error["pos"]
            error_desc = error["desc"]
            id = one["id"]

            conversation = {
                "id": f"{id}-{idx + 1}",
                "conversations": [
                    {
                        "from": "human",
                        # leetcode 相关描述: 一个 class Solution
                        # 保险语句: 加上 #include <bits/stdc++.h>, using namespace std; main
                        # cpp program -> cpp class?
                        "value": f"Could you provide a C++ program template with a class named 'Solution' and a 'main' function? The problem it should address is described as follows:\n{description}.\nPlease ensure to include the directive '#include <bits/stdc++.h>' and 'using namespace std;'.",
                    },
                    {
                        "from": "gpt",
                        "value": f"Sure, here is a cpp program for this problem:\n{error_code}\n{fmain}",
                    },
                    {
                        "from": "human",
                        "value": f"There is a bug in {row}:{col}, bug description is '{error_desc}', please fix it.",
                    },
                    {
                        "from": "gpt",
                        "value": f"Sorry, here is the fixed code:\n{answer}\n{fmain}",
                    },
                ],
            }

            result.append(conversation)

        return result
