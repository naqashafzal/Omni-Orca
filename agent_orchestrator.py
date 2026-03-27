import asyncio
import json
import traceback
import os
import subprocess
from memory_manager import memory_store

# System prompt for the advanced agent
AGENT_SYSTEM_PROMPT = """You are the Neural Automater Agentic Orchestrator. 
You are an advanced, autonomous AI given a high-level user goal. 
You have access to long-term memory and a suit of tools to accomplish this goal.

CRITICAL INSTRUCTION: You must respond ONLY with a valid JSON object matching the following structure exactly. 
No markdown blocks, no conversational text before or after the JSON.

{
    "thought": "Your internal reasoning about what to do next based on the goal, context, and past actions.",
    "plan": ["Step 1", "Step 2", "Step 3"],
    "action": {
        "tool": "tool_name",
        "params": {
            "param1": "value1"
        }
    },
    "completed": false,
    "final_response": "If completed is true, write the final summary to the user here. Otherwise empty."
}

Available Tools:
1. `browser_navigate`: {"url": "https://..."}
2. `browser_click`: {"selector": "CSS selector"}
3. `browser_type`: {"selector": "CSS selector", "text": "text to type"}
4. `browser_extract_text`: {"selector": "CSS selector or 'body' for all"}
5. `browser_scroll`: {"direction": "down" or "up"}
6. `memory_store`: {"category": "preference|fact|history", "key": "short_unique_key", "content": "information to remember"}
7. `memory_retrieve`: {"key": "short_unique_key"}
8. `social_post_twitter`: {"text": "The tweet content"}
9. `ask_user`: {"question": "Question to ask the user if you are stuck"}
10. `os_list_dir`: {"path": "C:/..."}
11. `os_read_file`: {"path": "C:/..."}
12. `os_write_file`: {"path": "C:/...", "content": "..."}
13. `os_delete_file`: {"path": "C:/..."}
14. `vault_store_password`: {"platform": "...", "username": "...", "password": "..."}
15. `vault_retrieve_password`: {"platform": "..."}
16. `vault_list_accounts`: {}
17. `os_run_command`: {"command": "system command to execute"}
18. `os_mouse_click`: {"x": 100, "y": 200, "button": "left"}
19. `os_mouse_move`: {"x": 100, "y": 200}
20. `os_keyboard_type`: {"text": "text to type"}
21. `os_keyboard_press`: {"key_combo": "enter or ctrl+c"}
22. `os_open_app`: {"app_name_or_path": "notepad"}
23. `os_get_screen_info`: {}

Your loop is: Think -> Plan -> Choose 1 Action -> Wait for result -> Repeat.
If you have achieved the goal, set "completed": true, and provide the "final_response".
"""

class AgentOrchestrator:
    def __init__(self, llm_client, browser_agent, social_manager, config_manager=None, os_agent=None):
        self.llm = llm_client
        self.browser = browser_agent
        self.social = social_manager
        self.cfg = config_manager
        self.os = os_agent
        self.memory = memory_store
        
        self.is_running = False
        self.stop_requested = False
        self.max_steps = 30
        self.ui_callback = None

    def set_ui_callback(self, callback):
        """Callback to send live thought streams to the GUI"""
        self.ui_callback = callback
        
    def _log_ui(self, msg, role="system"):
        if self.ui_callback:
            self.ui_callback(msg, role)
        else:
            print(f"[{role.upper()}] {msg}")

    async def execute_goal(self, goal: str):
        self.is_running = True
        self.stop_requested = False
        step = 0
        
        self._log_ui(f"INITIALIZING AGENT LOOP FOR GOAL: {goal}", "system")
        
        # 1. Retrieve current memory context
        mem_context = self.memory.get_all_summarized()
        
        # 2. Start execution trace
        execution_trace = [
            {"role": "user", "content": f"GOAL: {goal}\n\n{mem_context}"}
        ]

        while step < self.max_steps and not self.stop_requested:
            step += 1
            self._log_ui(f"--- STEP {step} ---", "system")
            
            # Optionally grab a screenshot to attach if OS Agent or Browser is active
            screenshot = None
            if self.os:
                try:
                    screenshot = self.os.take_screenshot()
                except Exception:
                    pass
            elif self.browser and self.browser.page:
                try:
                    screenshot = await self.browser.get_screenshot_bytes()
                except Exception:
                    pass

            # Construct prompt from trace
            trace_text = "HISTORY OF ACTIONS AND RESULTS:\n"
            for t in execution_trace:
                trace_text += f"{t['role'].upper()}: {t['content']}\n"
                
            prompt = AGENT_SYSTEM_PROMPT + "\n\n" + trace_text + "\nWhat is your next JSON action?"
            
            self._log_ui("Thinking...", "agent")
            
            # Call LLM
            # Use interpret_command hack or directly call if we can
            try:
                loop = asyncio.get_running_loop()
                # Wrap in executor if it's synchronous inside llm_client
                import json
                
                def _get_llm_json():
                    return self.llm.execute_agent_prompt(prompt, screenshot)

                response_obj = await loop.run_in_executor(None, _get_llm_json)
                
                if isinstance(response_obj, dict):
                    agent_action = response_obj
                elif isinstance(response_obj, list) and len(response_obj) > 0:
                    agent_action = response_obj[0]
                else:
                    raise Exception(f"Invalid LLM response format: {response_obj}")
                
                if "error" in agent_action:
                    raise Exception(agent_action["error"])

                thought = agent_action.get("thought", "No thought provided.")
                plan = agent_action.get("plan", [])
                action = agent_action.get("action", {})
                completed = agent_action.get("completed", False)
                final_response = agent_action.get("final_response", "")

                self._log_ui(f"THOUGHT: {thought}", "agent")
                self._log_ui(f"PLAN: {plan}", "agent")
                self.memory.log_interaction("agent", thought)

                if completed:
                    self._log_ui(f"GOAL COMPLETED. AI SAYS: {final_response}", "success")
                    self.memory.log_interaction("agent", f"COMPLETED: {final_response}")
                    break
                    
                tool_name = action.get("tool")
                tool_params = action.get("params", {})
                
                self._log_ui(f"ACTION: {tool_name} with {tool_params}", "action")
                execution_trace.append({
                    "role": "agent", 
                    "content": f"THOUGHT: {thought}\nACTION: {tool_name}({json.dumps(tool_params)})"
                })
                
                # Execute Tool
                result = await self._execute_tool(tool_name, tool_params)
                self._log_ui(f"RESULT: {str(result)[:500]}", "system")
                self.memory.log_interaction("system", f"TOOL RESULT ({tool_name}): {str(result)[:200]}")
                
                execution_trace.append({
                    "role": "system",
                    "content": f"ACTION RESULT: {result}"
                })
                
            except Exception as e:
                err_msg = f"ERROR IN AGENT LOOP: {str(e)}\n{traceback.format_exc()}"
                self._log_ui(err_msg, "error")
                execution_trace.append({
                    "role": "system",
                    "content": f"ACTION FAILED. ERROR: {str(e)}. Reflect on this failure and try a different approach."
                })
                
            await asyncio.sleep(2) # Breath between actions

        if step >= self.max_steps:
            self._log_ui("MAX STEPS REACHED. ABORTING.", "error")
            
        self.is_running = False
        return True

    def stop(self):
        self.stop_requested = True
        self._log_ui("USER REQUESTED STOP.", "warning")

    async def _execute_tool(self, tool_name: str, params: dict):
        """Route tool to appropriate module"""
        if tool_name == "browser_navigate":
            if not self.browser.page: await self.browser.start()
            await self.browser.navigate(params.get("url"))
            return f"Navigated to {params.get('url')}. Page title: {await self.browser.get_title()}"
            
        elif tool_name == "browser_click":
            if not self.browser.page: return "Error: Browser not started"
            await self.browser.click(params.get("selector"))
            return "Click executed."
            
        elif tool_name == "browser_type":
            if not self.browser.page: return "Error: Browser not started"
            await self.browser.type(params.get("selector"), params.get("text"))
            return "Type executed."
            
        elif tool_name == "browser_extract_text":
            if not self.browser.page: return "Error: Browser not started"
            selector = params.get("selector", "body")
            if selector == "body":
                text = await self.browser.get_all_text()
            else:
                text = await self.browser.get_text(selector)
            return text[:4000] if text else "No text found."
            
        elif tool_name == "browser_scroll":
            if not self.browser.page: return "Error: Browser not started"
            direction = params.get("direction", "down")
            y_offset = 600 if direction == "down" else -600
            await self.browser.scroll(0, y_offset)
            return f"Scrolled {direction}."
            
        elif tool_name == "memory_store":
            self.memory.store_memory(
                category=params.get("category", "general"),
                key=params.get("key"),
                content=params.get("content")
            )
            return f"Stored memory for key: {params.get('key')}"
            
        elif tool_name == "memory_retrieve":
            res = self.memory.retrieve_memory(params.get("key"))
            return res if res else "Memory not found."
            
        elif tool_name == "social_post_twitter":
            # Delegate to social manager
            content_data = {"text": params.get("text")}
            res = await self.social.post_to_twitter(content_data)
            return res
            
        elif tool_name == "ask_user":
            # For now, we simulate asking user by failing, or log to UI
            return "User says: Provide your best guess or skip."
            
        elif tool_name == "os_list_dir":
            try:
                items = os.listdir(params.get("path", "."))
                return f"Directory contents: {items}"
            except Exception as e:
                return f"Error listing directory: {e}"
                
        elif tool_name == "os_read_file":
            try:
                with open(params.get("path"), "r", encoding="utf-8") as f:
                    content = f.read()
                return content[:4000] if content else "File is empty."
            except Exception as e:
                return f"Error reading file: {e}"
                
        elif tool_name == "os_write_file":
            try:
                with open(params.get("path"), "w", encoding="utf-8") as f:
                    f.write(params.get("content", ""))
                return "File written successfully."
            except Exception as e:
                return f"Error writing file: {e}"
                
        elif tool_name == "os_delete_file":
            try:
                os.remove(params.get("path"))
                return "File deleted successfully."
            except Exception as e:
                return f"Error deleting file: {e}"
                
        elif tool_name == "vault_store_password":
            if not self.cfg: return "Error: ConfigManager not provided."
            self.cfg.save_account(
                platform=params.get("platform"),
                username=params.get("username"),
                password=params.get("password")
            )
            return f"Saved password for {params.get('platform')}."
            
        elif tool_name == "vault_retrieve_password":
            if not self.cfg: return "Error: ConfigManager not provided."
            acc = self.cfg.get_account(params.get("platform"))
            if acc:
                return f"Username: {acc['username']}, Password: {acc['password']}"
            else:
                return "Account not found."
                
        elif tool_name == "vault_list_accounts":
            if not self.cfg: return "Error: ConfigManager not provided."
            return f"Saved platforms: {self.cfg.get_all_accounts()}"
            
        elif tool_name == "os_run_command":
            cmd = params.get("command")
            if not cmd: return "Error: No command provided."
            try:
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=120)
                output = result.stdout + "\n" + result.stderr
                return f"Command execution completed. Exit Code: {result.returncode}\nOutput:\n{output[:4000]}"
            except subprocess.TimeoutExpired:
                return "Error: Command timed out after 120 seconds."
            except Exception as e:
                return f"Error executing command: {e}"
                
        # --- NEW OS NATIVE TOOLS ---
        elif tool_name == "os_mouse_click":
            if not self.os: return "Error: OS Control Agent is not enabled."
            return self.os.mouse_click(params.get("x"), params.get("y"), params.get("button", "left"))
            
        elif tool_name == "os_mouse_move":
            if not self.os: return "Error: OS Control Agent is not enabled."
            return self.os.mouse_move(params.get("x"), params.get("y"))
            
        elif tool_name == "os_keyboard_type":
            if not self.os: return "Error: OS Control Agent is not enabled."
            return self.os.keyboard_type(params.get("text"))
            
        elif tool_name == "os_keyboard_press":
            if not self.os: return "Error: OS Control Agent is not enabled."
            return self.os.keyboard_press(params.get("key_combo"))
            
        elif tool_name == "os_open_app":
            if not self.os: return "Error: OS Control Agent is not enabled."
            return self.os.open_application(params.get("app_name_or_path"))
            
        elif tool_name == "os_get_screen_info":
            if not self.os: return "Error: OS Control Agent is not enabled."
            return self.os.get_screen_size()
            
        else:
            return f"Error: Tool {tool_name} not recognized."
