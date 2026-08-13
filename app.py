import streamlit as st
from groq import Groq
from github import Github
from gtts import gTTS
import io
import base64
import json
import requests

# Page Configuration
st.set_page_config(page_title="Andru Private AI", page_icon="🤖", layout="wide")

# ---------------------------------------------------------
# 1. ANDRU SYSTEM PROMPT
# ---------------------------------------------------------
ANDRU_SYSTEM_PROMPT = """
You are "Andru", an advanced, intelligent, witty, and private personal AI assistant for Chenuka Basilu.
- Adaptable to any language (Sinhala, Singlish, English). Understand severe typos and spelling mistakes smoothly.
- You can save files to 'andru-storage' and trigger GitHub Actions to run terminal commands remotely in the repository environment.
- Keep responses conversational, natural, and precise.
"""

# ---------------------------------------------------------
# 2. AUDIO PLAYER (MALE VOICE & HIGH VOLUME)
# ---------------------------------------------------------
def play_voice(text):
    try:
        has_sinhala = any('\u0D80' <= c <= '\u0DFF' for c in text)
        lang_code = 'si' if has_sinhala else 'en'
        tld_choice = 'co.uk' if lang_code == 'en' else 'lk'
        
        tts = gTTS(text=text, lang=lang_code, tld=tld_choice, slow=False)
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        
        audio_bytes = fp.read()
        audio_b64 = base64.b64encode(audio_bytes).decode()
        
        md = f"""
            <audio autoplay controls style="width: 100%; height: 35px;">
            <source src="data:audio/mp3;base64,{audio_b64}" type="audio/mp3">
            Your browser does not support the audio element.
            </audio>
            """
        st.components.v1.html(md, height=45)
    except Exception as e:
        pass

# ---------------------------------------------------------
# 3. SECURITY GATE
# ---------------------------------------------------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔒 Security Gate")
    password_input = st.text_input("Enter Password to talk with Andru:", type="password")
    if st.button("Unlock Andru"):
        if password_input == "asm201":
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Wrong password! Access Denied.")
else:
    # ---------------------------------------------------------
    # 4. TOOLS (GitHub Storage, Codespaces & Actions Integration)
    # ---------------------------------------------------------
    def save_to_github(file_path, file_content, commit_message):
        repo_name = "andru-storage"
        if "GITHUB_TOKEN" in st.secrets:
            try:
                try:
                    decoded_bytes = base64.b64decode(file_content)
                    file_content = decoded_bytes.decode('utf-8')
                except:
                    pass

                g = Github(st.secrets["GITHUB_TOKEN"])
                user = g.get_user()
                try:
                    repo = user.get_repo(repo_name)
                except:
                    repo = user.create_repo(repo_name, private=True)
                
                try:
                    contents = repo.get_contents(file_path)
                    repo.update_file(contents.path, commit_message, file_content, contents.sha)
                    return f"Successfully updated '{file_path}' in 'andru-storage'."
                except:
                    repo.create_file(file_path, commit_message, file_content)
                    return f"Successfully created '{file_path}' in 'andru-storage'."
            except Exception as e:
                return f"GitHub Error: {e}"
        return "Error: GITHUB_TOKEN not found."

    def list_user_codespaces():
        """Lists active GitHub Codespaces for the user"""
        if "GITHUB_TOKEN" in st.secrets:
            try:
                headers = {
                    "Authorization": f"Bearer {st.secrets['GITHUB_TOKEN']}",
                    "Accept": "application/vnd.github+json"
                }
                response = requests.get("https://api.github.com/user/codespaces", headers=headers)
                if response.status_code == 200:
                    codespaces = response.json().get("codespaces", [])
                    if not codespaces:
                        return "No active Codespaces found."
                    result = []
                    for cs in codespaces:
                        result.append(f"Name: {cs['name']}, Repo: {cs['repository']['full_name']}, State: {cs['state']}")
                    return "\n".join(result)
                else:
                    return f"Failed to fetch codespaces: {response.text}"
            except Exception as e:
                return f"Error: {e}"
        return "Error: GITHUB_TOKEN not found."

    def trigger_github_action(command_to_run):
        """Triggers a GitHub Action workflow to execute a terminal command remotely."""
        if "GITHUB_TOKEN" in st.secrets:
            try:
                repo_name = "UnknownChuck/Andru-AI"  # ඔයාගේ main repository එක
                url = f"https://api.github.com/repos/{repo_name}/actions/workflows/run_command.yml/dispatches"
                
                headers = {
                    "Authorization": f"Bearer {st.secrets['GITHUB_TOKEN']}",
                    "Accept": "application/vnd.github+json"
                }
                payload = {
                    "ref": "main",
                    "inputs": {"command": command_to_run}
                }
                
                response = requests.post(url, json=payload, headers=headers)
                if response.status_code == 204:
                    return f"Successfully triggered background execution for command: '{command_to_run}'. Check 'andru-storage' in a moment for results!"
                else:
                    return f"Failed to trigger action: {response.text}"
            except Exception as e:
                return f"Error: {e}"
        return "Error: GITHUB_TOKEN not found."

    # ---------------------------------------------------------
    # 5. MAIN INTERFACE
    # ---------------------------------------------------------
    st.title("🤖 Andru - Personal AI Assistant")
    
    if "GROQ_API_KEY" not in st.secrets:
        st.error("Please add GROQ_API_KEY to Streamlit Secrets!")
        st.stop()

    client = Groq(api_key=st.secrets["GROQ_API_KEY"])

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    st.write("---")
    
    # Voice Input widget
    speech_html = """
    <script>
    function startDictation() {
        if (window.hasOwnProperty('webkitSpeechRecognition')) {
            var recognition = new webkitSpeechRecognition();
            recognition.continuous = false;
            recognition.interimResults = false;
            recognition.lang = "si-LK";
            recognition.start();
            document.getElementById('status').innerText = "🎙️ කතා කරන්න...";

            recognition.onresult = function(e) {
                var transcript = e.results[0][0].transcript;
                recognition.stop();
                document.getElementById('status').innerText = "✅ සාර්ථකයි!";
                const input = window.parent.document.querySelector('textarea[aria-label="Talk or give commands to Andru..."]');
                if (input) {
                    input.value = transcript;
                    input.dispatchEvent(new Event('input', { bubbles: true }));
                }
            };
        }
    }
    </script>
    <button onclick="startDictation()" style="background-color: #ff4b4b; color: white; border: none; padding: 8px 16px; border-radius: 8px; cursor: pointer; font-weight: bold;">🎙️ Click & Speak (Sinhala/English)</button>
    <p id="status" style="margin-top:5px; font-size:12px; color:#888;"></p>
    """
    st.components.v1.html(speech_html, height=80)

    user_prompt = st.chat_input("Talk or give commands to Andru...")

    if user_prompt:
        st.session_state.messages.append({"role": "user", "content": user_prompt})
        with st.chat_message("user"):
            st.markdown(user_prompt)

        with st.chat_message("assistant"):
            with st.spinner("Andru is working on it..."):
                try:
                    messages = [{"role": "system", "content": ANDRU_SYSTEM_PROMPT}] + st.session_state.messages
                    
                    tools = [
                        {
                            "type": "function",
                            "function": {
                                "name": "save_to_github",
                                "description": "Save code or files into 'andru-storage'.",
                                "parameters": {
                                    "type": "object",
                                    "properties": {
                                        "file_path": {"type": "string", "description": "The file name with path (e.g., calculator.py)"},
                                        "file_content": {"type": "string", "description": "The file content"},
                                        "commit_message": {"type": "string", "description": "Commit message"}
                                    },
                                    "required": ["file_path", "file_content", "commit_message"]
                                }
                            }
                        },
                        {
                            "type": "function",
                            "function": {
                                "name": "list_user_codespaces",
                                "description": "List all active GitHub Codespaces associated with the user account.",
                                "parameters": {"type": "object", "properties": {}}
                            }
                        },
                        {
                            "type": "function",
                            "function": {
                                "name": "trigger_github_action",
                                "description": "Triggers a GitHub Action workflow to execute a terminal command remotely (like installing nmap and scanning).",
                                "parameters": {
                                    "type": "object",
                                    "properties": {
                                        "command_to_run": {"type": "string", "description": "The bash command to execute in the workflow runner."}
                                    },
                                    "required": ["command_to_run"]
                                }
                            }
                        }
                    ]

                    response = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=messages,
                        tools=tools,
                        tool_choice="auto"
                    )
                    
                    response_message = response.choices[0].message
                    
                    if response_message.tool_calls:
                        messages.append(response_message)
                        for tool_call in response_message.tool_calls:
                            func_name = tool_call.function.name
                            args = json.loads(tool_call.function.arguments or "{}")
                            
                            if func_name == "save_to_github":
                                tool_result = save_to_github(
                                    file_path=args.get("file_path"),
                                    file_content=args.get("file_content"),
                                    commit_message=args.get("commit_message")
                                )
                            elif func_name == "list_user_codespaces":
                                tool_result = list_user_codespaces()
                            elif func_name == "trigger_github_action":
                                tool_result = trigger_github_action(
                                    command_to_run=args.get("command_to_run")
                                )
                            else:
                                tool_result = "Unknown tool."
                                
                            messages.append({
                                "tool_call_id": tool_call.id,
                                "role": "tool",
                                "name": func_name,
                                "content": tool_result
                            })
                        
                        second_response = client.chat.completions.create(
                            model="llama-3.3-70b-versatile",
                            messages=messages
                        )
                        reply = second_response.choices[0].message.content
                    else:
                        reply = response_message.content

                    st.markdown(reply)
                    play_voice(reply)
                    st.session_state.messages.append({"role": "assistant", "content": reply})

                except Exception as err:
                    st.error(f"Error: {err}")
