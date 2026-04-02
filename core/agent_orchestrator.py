import asyncio
import json
import traceback
import os
import subprocess
from core.memory_manager import memory_store
from agents.memory_agent import MemoryAgent
from tools.document_indexer import DocumentIndexer
from agents.web_search_agent import WebSearchAgent
from agents.email_agent import EmailAgent
from agents.calendar_agent import CalendarAgent
from agents.call_agent import CallAgent

BASE_JSON_FORMAT = """
CRITICAL INSTRUCTION: You must respond ONLY with a valid JSON object matching the following structure exactly. 
No markdown blocks, no conversational text before or after the JSON.

{
    "thought": "Your internal reasoning.",
    "plan": ["Step 1", "Step 2"],
    "action": {"tool": "tool_name", "params": {"param1": "value1"}},
    "completed": false,
    "final_response": "If completed is true, write the final summary here."
}
Your loop is: Think -> Plan -> Choose 1 Action -> Wait for result -> Repeat.
"""

SUPERVISOR_PROMPT = """You are Omni-Orca, the Supervisor Agent of the Neural Swarm.
Your job is to break the user's goal into steps and DELEGATE them to appropriate specialists.
When all steps are finished, report the final completion.
Available Tools:
1. `delegate_to_coder`: {"task": "Write python script or search files..."}
2. `delegate_to_browser`: {"task": "Search google for weather..."}
3. `delegate_to_os`: {"task": "Click the start menu..."}
4. `ltm_memorize`: {"fact": "fact to remember"}
5. `ltm_recall`: {"query": "Search long-term memory"}
6. `email_get_unread`: {"n": 5}
7. `email_send`: {"to": "...", "subject": "...", "body": "..."}
8. `calendar_get_events`: {"n": 5}
9. `calendar_create_event`: {"title": "...", "date": "YYYY-MM-DD", "start_time": "HH:MM"}
10. `call_phone`: {"to_number": "+923001234567", "message": "spoken message"}
11. `send_sms`: {"to_number": "+92...", "message": "text message"}
12. `web_search`: {"query": "latest gold price"}
13. `web_fetch_page`: {"url": "https://..."}
14. `search_news`: {"query": "AI news today"}
""" + BASE_JSON_FORMAT

CODER_PROMPT = """You are the Coder Agent. 
You specialize in reading, writing, and executing code and semantic RAG searches.
Available Tools:
1. `os_list_dir`: {"path": "C:/..."}
2. `os_read_file`: {"path": "C:/..."}
3. `os_write_file`: {"path": "C:/...", "content": "..."}
4. `os_delete_file`: {"path": "C:/..."}
5. `os_run_command`: {"command": "python script.py"}
6. `rag_index_folder`: {"folder_path": "C:/..."}
7. `rag_search`: {"query": "keywords to search"}
""" + BASE_JSON_FORMAT

BROWSER_PROMPT = """You are the Browser Agent.
You specialize in navigating the web and scraping data using Playwright.
Available Tools:
1. `browser_navigate`: {"url": "https://..."}
2. `browser_click`: {"selector": "CSS selector"}
3. `browser_type`: {"selector": "CSS selector", "text": "text"}
4. `browser_extract_text`: {"selector": "body"}
5. `browser_scroll`: {"direction": "down"}
6. `social_post_twitter`: {"text": "tweet text"}
7. `web_search`: {"query": "search query"}
8. `web_fetch_page`: {"url": "https://..."}
9. `search_news`: {"query": "topic"}
""" + BASE_JSON_FORMAT

OS_PROMPT = """You are the OS Agent.
You specialize in physically controlling the user's mouse and keyboard in God Mode.
Available Tools:
1. `os_mouse_click`: {"x": 100, "y": 200, "button": "left"}
2. `os_mouse_move`: {"x": 100, "y": 200}
3. `os_keyboard_type`: {"text": "text"}
4. `os_keyboard_press`: {"key_combo": "enter"}
5. `os_open_app`: {"app_name_or_path": "notepad"}
6. `os_get_screen_info`: {}
""" + BASE_JSON_FORMAT

class AgentOrchestrator:
    def __init__(self, llm_client, browser_agent, social_manager, config_manager=None, os_agent=None):
        self.llm = llm_client
        self.browser = browser_agent
        self.social = social_manager
        self.cfg = config_manager
        self.os = os_agent
        self.stm = memory_store  # Short term context
        self.ltm = MemoryAgent() # Persistent Vector Space
        self.rag = DocumentIndexer() # RAG Document Search
        self.web = WebSearchAgent() # Real-time Web Search
        self.email = EmailAgent()   # Gmail integration
        self.calendar = CalendarAgent() # Google Calendar
        self.calls = CallAgent()    # Twilio phone/SMS
        
        
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
        
        self._log_ui(f"INITIALIZING NEURAL SWARM SUPERVISOR FOR GOAL: {goal}", "system")
        
        stm_context = self.stm.get_all_summarized()
        ltm_facts = self.ltm.recall(goal, n_results=5)
        ltm_context = "LONG-TERM MEMORY RELEVANT FACTS:\n" + "\n".join(ltm_facts) if ltm_facts else "No prior history available."
        
        # Start top-level Supervisor loop
        return await self._execute_sub_agent(SUPERVISOR_PROMPT, f"GOAL: {goal}\n\n{ltm_context}\n\nSHORT-TERM CONTEXT:\n{stm_context}", "SUPERVISOR")

    async def _execute_sub_agent(self, system_prompt: str, task: str, role_name: str, max_steps: int = 15):
        step = 0
        execution_trace = [{"role": "user", "content": task}]

        while step < max_steps and not self.stop_requested:
            step += 1
            self._log_ui(f"--- [{role_name}] STEP {step} ---", "system")
            
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
                
            prompt = system_prompt + "\n\n" + trace_text + "\nWhat is your next JSON action?"
            
            self._log_ui(f"{role_name} Thinking...", "agent")
            
            # Call LLM
            try:
                loop = asyncio.get_running_loop()
                import json
                
                def _get_llm_json():
                    return self.llm.execute_agent_prompt(prompt, screenshot)

                fut = loop.run_in_executor(None, _get_llm_json)
                while not fut.done():
                    if self.stop_requested:
                        self._log_ui("USER STOP REQUESTED. HALTING NEURAL BRAIN...", "warning")
                        return "Aborted"
                    await asyncio.sleep(0.5)
                    
                response_obj = fut.result()
                
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
                self.stm.log_interaction("agent", thought)

                if completed:
                    self._log_ui(f"GOAL COMPLETED. AI SAYS: {final_response}", "success")
                    self.stm.log_interaction("agent", f"COMPLETED: {final_response}")
                    break
                    
                tool_name = action.get("tool")
                tool_params = action.get("params", {})
                
                self._log_ui(f"ACTION: {tool_name} with {tool_params}", "action")
                execution_trace.append({
                    "role": "agent", 
                    "content": f"THOUGHT: {thought}\nACTION: {tool_name}({json.dumps(tool_params)})"
                })
                
                # Swarm Delegation Overrides
                if tool_name == "delegate_to_coder":
                    self._log_ui(f"Supervisor dispatching CoderAgent -> {tool_params.get('task')}", "action")
                    result = await self._execute_sub_agent(CODER_PROMPT, tool_params.get('task'), "CODER", max_steps=10)
                elif tool_name == "delegate_to_browser":
                    self._log_ui(f"Supervisor dispatching BrowserAgent -> {tool_params.get('task')}", "action")
                    result = await self._execute_sub_agent(BROWSER_PROMPT, tool_params.get('task'), "BROWSER", max_steps=10)
                elif tool_name == "delegate_to_os":
                    self._log_ui(f"Supervisor dispatching OSAgent -> {tool_params.get('task')}", "action")
                    result = await self._execute_sub_agent(OS_PROMPT, tool_params.get('task'), "OS", max_steps=10)
                else:
                    # Normal Execute Tool
                    result = await self._execute_tool(tool_name, tool_params)
                    
                self._log_ui(f"[{role_name}] RESULT: {str(result)[:500]}", "system")
                self.stm.log_interaction("system", f"TOOL RESULT ({tool_name}): {str(result)[:200]}")
                
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

        if step >= max_steps:
            self._log_ui(f"[{role_name}] MAX STEPS REACHED. ABORTING.", "error")
            return f"Error: {role_name} failed to complete task within max steps."
            
        return "Internal abort."

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
            
        elif tool_name == "ltm_memorize":
            fact = params.get("fact")
            if not fact: return "Error: Missing fact parameter."
            return self.ltm.memorize(fact, source="Agent Orchestrator")
            
        elif tool_name == "ltm_recall":
            query = params.get("query")
            if not query: return "Error: Missing query parameter."
            facts = self.ltm.recall(query, n_results=3)
            return "Found facts:\n" + "\n".join(facts) if facts else "No facts found."
            
        elif tool_name == "social_post_twitter":
            # Delegate to social manager
            content_data = {"text": params.get("text")}
            res = await self.social.post_to_twitter(content_data)
            return res
            
        elif tool_name == "rag_index_folder":
            folder = params.get("folder_path")
            if not folder: return "Error: Missing folder_path."
            return self.rag.index_folder(folder)
            
        elif tool_name == "rag_search":
            query = params.get("query")
            if not query: return "Error: Missing query parameter."
            return self.rag.search(query)
            
        # --- V3: Web Search ---
        elif tool_name == "web_search":
            return self.web.search(params.get("query", ""))
        elif tool_name == "web_fetch_page":
            return self.web.fetch_page_text(params.get("url", ""))
        elif tool_name == "search_news":
            return self.web.search_news(params.get("query", ""))

        # --- V3: Email ---
        elif tool_name == "email_get_unread":
            return self.email.get_unread(int(params.get("n", 5)))
        elif tool_name == "email_send":
            return self.email.send_email(params.get("to", ""), params.get("subject", ""), params.get("body", ""))
        elif tool_name == "email_search":
            return self.email.search_emails(params.get("keyword", ""))

        # --- V3: Calendar ---
        elif tool_name == "calendar_get_events":
            return self.calendar.get_upcoming_events(int(params.get("n", 5)))
        elif tool_name == "calendar_create_event":
            return self.calendar.create_event(params.get("title", "Meeting"), params.get("date", ""), params.get("start_time", "09:00"), params.get("end_time"), params.get("description", ""))
        elif tool_name == "calendar_briefing":
            return self.calendar.get_todays_briefing()

        # --- V3: Phone/SMS ---
        elif tool_name == "call_phone":
            return self.calls.make_call(params.get("to_number", ""), params.get("message", ""))
        elif tool_name == "send_sms":
            return self.calls.send_sms(params.get("to_number", ""), params.get("message", ""))

        elif tool_name == "ask_user":
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
