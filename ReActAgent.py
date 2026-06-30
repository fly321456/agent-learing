import json
from typing import Dict, Any

class ReActAgent:
    def __init__(self, tools: dict, state_file: str = "agent_state.json"):
        self.tools = tools  # 可用工具字典
        self.state_file = state_file
        self.max_steps = 10  # 防止无限循环

    def observe(self, state: Dict) -> Dict:
        """观察：整合当前所有信息（用户输入、上一步结果、记忆）"""
        # 这里可以接入你的本地记忆系统（如 SQLite 读取历史）
        return state

    def think(self, state: Dict) -> str:
        """思考：LLM 根据观察决定下一步动作（伪代码）"""
        # 1. 构建 Prompt：描述目标、可用工具、历史
        prompt = f"""
        目标：{state['goal']}
        可用工具：{list(self.tools.keys())}
        历史步骤：{state.get('history', [])[-3:]}  # 最近3步
        请决定下一步动作（格式：tool_name 或 FINISH）：
        """
        # 2. 调用 LLM（此处简化）
        if "未完成" in state.get('last_result', ''):
            return "continue_processing"  # 模拟 LLM 决策
        return "FINISH"

    def act(self, action: str, state: Dict) -> Dict:
        """执行：调用工具并更新状态"""
        if action == "FINISH":
            state['status'] = 'completed'
            return state
        
        # 调用工具（你的工作流节点）
        tool = self.tools.get(action)
        if tool:
            result = tool(state.get('data'))
            state['last_result'] = result
            state['history'].append(f"执行 {action}: {result}")
        
        return state

    def run(self, initial_goal: str):
        """运行主循环（支持断点续跑）"""
        # 尝试从本地文件加载状态（实现持久化）
        try:
            with open(self.state_file, 'r') as f:
                state = json.load(f)
            print("检测到历史状态，恢复运行...")
        except FileNotFoundError:
            state = {'goal': initial_goal, 'history': [], 'step': 0}
        
        while state.get('status') != 'completed' and state['step'] < self.max_steps:
            state['step'] += 1
            
            # 1. OBSERVE
            current_state = self.observe(state)
            
            # 2. THINK
            action = self.think(current_state)
            print(f"[Step {state['step']}] 决策: {action}")
            
            # 3. ACT
            state = self.act(action, state)
            
            # 4. 保存状态到本地（实现 Checkpoint）
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
            
            # 新的 OBSERVE 隐含在下一轮循环的 observe() 中
        
        return state

# 使用示例
def my_summarize_tool(text):
    return f"已总结: {text[:100]}..."

agent = ReActAgent(tools={'summarize': my_summarize_tool})
result = agent.run("处理文档并生成报告")