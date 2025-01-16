import streamlit as st
import sqlite3
import json
from hashlib import sha256
from groq import Groq
import time
import asyncio


conn = sqlite3.connect("users.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password TEXT,
    progress INTEGER
)
""")
conn.commit()

def hash_password(password):
    return sha256(password.encode()).hexdigest()

def signup_sql(username, password):
    hashed_password = hash_password(password)
    try:
        cursor.execute("INSERT INTO users (username, password, progress) VALUES (?, ?, ?)", 
                       (username, hashed_password, 0)) 
        conn.commit()
        return True, "Account created successfully!"
    except sqlite3.IntegrityError:
        return False, "Username already exists!"

def login_sql(username, password):
    cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    if not result:
        return False, "Username does not exist!"
    if result[0] != hash_password(password):
        return False, "Incorrect password!"
    return True, "Login successful!"

def save_progress_sql(username, progress):
    cursor.execute("UPDATE users SET progress = ? WHERE username = ?", (progress, username))
    conn.commit()

def load_progress_sql(username):
    cursor.execute("SELECT progress FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    return result[0] if result else None

async def countdown_timer(seconds):
    while seconds > 0:
        st.session_state.timer_running = f"Time Remaining: {seconds} seconds"
        seconds -= 1
        await asyncio.sleep(1)
    st.session_state.timer_running = "Time's up!"

client = Groq(api_key=st.secrets["groq_api_key"])
def generate_story(level, difflevel):
    num_clues = max(3 - (level // 5), 1) 
    num_red_herrings = 2 + (level // 5) 


    prompt = (
        f"You are a mystery story generator. Create a random detective story for level {level} with:\n"
        f"- A setting (e.g., mansion, park, office).\n"
        f"- A description of what crime happened.\n"
        f"- A victim and their backstory.\n"
        f"- 4 suspects, each with motives and alibis.\n"
        f"- {num_clues} key clues.\n"
        f"- {num_red_herrings} red herrings.\n"
        f"- One culprit. \n"
        f"- An explanation of why the culprit committed the crime. \n"
        f"- Make it a {difflevel}. \n"
        "Provide the output in JSON format: \n"
        "{\n"
        "    \"setting\": \"\",\n"
        "    \"description\": \"\",\n"
        "    \"victim\": \"\",\n"
        "    \"suspects\": {\n"
        "        \"<Suspect 1 Full Name>\": \"\",\n"
        "        \"<Suspect 2 Full Name>\": \"\",\n"
        "        \"<Suspect 3 Full Name>\": \"\",\n"
        "        \"<Suspect 4 Full Name>\": \"\"\n"
        "    },\n"
        "    \"clues\": [],\n"
        "    \"red_herrings\": [],\n"
        "    \"culprit\": \"\",\n"
        "    \"explanation\": \"\"\n"
        "}\n"
        "Only output the JSON part. \n"
        "Only output the first and last name for the culprit, no prefixes such as Dr or Mr or Mrs or Ms. \n"
        "Don't explain why they are red herrings. \n"
    )


    completion = client.chat.completions.create(
        model="llama3-70b-8192",  
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=1,
        max_tokens=1024,
        top_p=1,
        stream=False,
        stop=None,
    )

    story = completion.choices[0].message.content
    return story

st.title("ClueQuest AI")
st.sidebar.header("Navigation")
menu = st.sidebar.selectbox("Menu", [ "Login", "Signup", "Level Mode"])

if "username" not in st.session_state:
    st.session_state.username = None
if "story" not in st.session_state:
    st.session_state.story = None
    st.session_state.current_stage = "start"
if "timer" not in st.session_state:
    st.session_state.timer = None


if menu == "Signup":
    if not st.session_state.username:
        st.subheader("Welcome to ClueQuest AI!")
        st.subheader("Sign Up")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Sign Up"):
            success, message = signup_sql(username, password)
            if success:
                st.success(message)
            else:
                st.error(message)
    else:
        st.success(f"Logged in as {st.session_state.username}")

elif menu == "Login":
    if not st.session_state.username:
        st.subheader("Welcome to ClueQuest AI!")
        st.subheader("Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            success, message = login_sql(username, password)
            if success:
                st.session_state.username = username
                st.success(message)
                st.sidebar.success(f"Logged in as {username}")
            else:
                st.error(message)
    else:
        st.success(f"Logged in as {st.session_state.username}")

elif menu == "Level Mode":
    bg_image = """
    <style>
    [data-testid="stAppViewContainer"] {
        background-image: url("https://www.psychologicalscience.org/redesign/wp-content/uploads/2022/01/How-Haunted-Houses-Measure-Fear-Web-1600x842.jpg");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }
    [data-testid="stHeader"] {
        background: rgba(0,0,0,0); /* Hides the header */
    }
    [data-testid="stSidebar"] {
        background: rgba(0,0,0,0.5); /* Makes the sidebar slightly transparent */
    }
    </style>
    """
    st.markdown(bg_image, unsafe_allow_html=True)
    if not st.session_state.username:
        st.text(" Welcome to ClueQuest AI!")
        st.warning("You must log in to play the game.")
    else:
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Log Out"):
                st.session_state.username = None
                st.session_state.running = False
                st.session_state.playing = True
                st.session_state.current_stage = "start"
                st.session_state.story = None
                st.rerun()

        st.subheader(f"Welcome, Detective {st.session_state.username}!")
        progress = load_progress_sql(st.session_state.username) or 0
        st.write(f"Current Level: {progress + 1}")

        if st.session_state.story is None:
            if st.button("Solve Mystery"):
                story_json = generate_story(progress + 1, "Medium")
                story = json.loads(story_json)  
                st.session_state.story = story
                st.session_state.culprit = story["culprit"]

        if st.session_state.story:
            story = st.session_state.story

            if st.session_state.current_stage == "start":
                st.subheader("You arrive at the scene of the crime.")
                setting = story['setting'].lower()
                st.write(f"You are at {setting}. {story['description']} The victim was {story['victim']}")
                st.write("What would you like to do?")
                if st.button("Look for clues"):
                    st.session_state.current_stage = "clue_hunt"
                if st.button("Talk to suspects"):
                    st.session_state.current_stage = "interview"
                st.rerun()

            elif st.session_state.current_stage == "clue_hunt":
                st.subheader("Looking for clues...")
                clue_labels = [f"Clue {i+1}" for i in range(len(story["clues"]))]
                clue_length = len(story["clues"]) 
                herring_labels = [f"Clue {i+clue_length+1}" for i in range(len(story['red_herrings']))]
                selected_clue_label = st.selectbox("Select a clue to investigate:", clue_labels + herring_labels)
                if int(selected_clue_label.split()[1]) <= len(story["clues"]):
                    selected_clue_index = clue_labels.index(selected_clue_label)
                    st.write(f"**Revealed Clue:** {story['clues'][selected_clue_index]}") 
                else:
                    selected_clue_index = herring_labels.index(selected_clue_label) - clue_length + 1
                    st.write(f"**Revealed Clue:** {story['red_herrings'][selected_clue_index]}") 

                st.write("What will you do now?")
                if st.button("Talk to suspects"):
                    st.session_state.current_stage = "interview"
                    st.rerun()
                if st.button("Guess the culprit"):
                    st.session_state.current_stage = "guess"
                    st.rerun()


            elif st.session_state.current_stage == "interview":
                st.subheader("Talking to suspects...")
                available_suspects = story['suspects']
                suspect = st.selectbox("Choose a suspect to talk to:", available_suspects)
                if st.button("Interrogate Suspect"):
                    st.write(f"Suspect: **{suspect}**")
                    st.write(f"Details: {story['suspects'][suspect]}")
 
                st.write("What will you do now?")       
                if st.button("Look for clues"):
                    st.session_state.current_stage = "clue_hunt"
                    st.rerun()
                if st.button("Guess the culprit"):
                    st.session_state.current_stage = "guess"
                    st.rerun()

                
            elif st.session_state.current_stage == "guess":
                button_text = "Submit Guess"
                st.subheader("Who is the culprit?")
                guess = st.selectbox("Accuse a suspect:", story['suspects'])
                if "guessing" not in st.session_state:
                    st.session_state.guessing = False
                if "playing" not in st.session_state:
                    st.session_state.playing = True
                if st.button(button_text, disabled=st.session_state.guessing, key='guess'):  
                    st.session_state.guessing = False
                    st.session_state.playing = False
                    if guess.lower() == story["culprit"].lower():
                        st.success(f"Correct! The culprit was {story['culprit']}.")
                        st.write(f"Explanation: {story['explanation']}")
                        save_progress_sql(st.session_state.username, progress + 1) 
                        
                    else:
                        st.error(f"Incorrect! You failed! The culprit was {story['culprit']}.")
                        st.write(f"Explanation: {story['explanation']}")

                if st.button("Play Again", disabled = st.session_state.playing, key='play_again'):
                    st.session_state.running = False
                    st.session_state.playing = True
                    st.session_state.current_stage = "start"
                    st.session_state.story = None
                    st.rerun()
               