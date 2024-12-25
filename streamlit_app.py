import streamlit as st
import sqlite3
import json
from hashlib import sha256
from groq import Groq

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

# Hashing Passwords
def hash_password(password):
    return sha256(password.encode()).hexdigest()

# Database Functions
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

client = Groq(api_key=st.secrets["groq_api_key"])
def generate_story(level):
    num_clues = max(3 - (level // 5), 1) 
    num_red_herrings = 2 + (level // 5) 


    prompt = (
        f"You are a mystery story generator. Create a random detective story for level {level} with:\n"
        f"- A setting (e.g., mansion, park, office).\n"
        f"- A victim and their backstory.\n"
        f"- 4 suspects, each with motives and alibis.\n"
        f"- {num_clues} key clues.\n"
        f"- {num_red_herrings} red herrings.\n"
        f"- One culprit. \n"
        f"- An explanation of why the culprit commited the crime. \n"
        "Provide the output in JSON format: \n"
        "{\n"
        "    \"setting\": \"\",\n"
        "    \"victim\": \"\",\n"
        "    \"suspects\": {\n"
        "        \"Suspect1\": \"\",\n"
        "        \"Suspect2\": \"\",\n"
        "        \"Suspect3\": \"\",\n"
        "        \"Suspect4\": \"\"\n"
        "    },\n"
        "    \"clues\": [],\n"
        "    \"red_herrings\": [],\n"
        "    \"culprit\": \"\"\n"
        "    \"explanation\": \"\"\n"
        "}"
        "Only output the JSON part. \n"
        "Only output the first and last name for the culprit. \n"
        "Output the clues and red_herrings together in clues, don't explain why they are red_herrings. \n"

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

# Streamlit App
st.title("ClueQuest AI")
st.sidebar.header("Navigation")
menu = st.sidebar.selectbox("Menu", ["Home", "Login", "Signup", "Game"])

# User Session State
if "username" not in st.session_state:
    st.session_state.username = None

if menu == "Home":
    st.subheader("Welcome to ClueQuest AI!")
    st.write("Login or sign up to start solving mysteries.")

elif menu == "Signup":
    st.subheader("Sign Up")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Sign Up"):
        success, message = signup_sql(username, password)
        st.success(message) if success else st.error(message)

elif menu == "Login":
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

elif menu == "Game":
    if not st.session_state.username:
        st.warning("You must log in to play the game.")
    else:
        st.subheader(f"Welcome, Detective {st.session_state.username}!")
        progress = load_progress_sql(st.session_state.username) or 0
        st.write(f"Current Level: {progress + 1}")
        
        if "story" not in st.session_state:
            st.session_state.story = None
            st.session_state.culprit = None
        
        if st.button("Generate Story"):
            story_json = generate_story(progress + 1)
            try:
                story = json.loads(story_json)  
                st.session_state.story = story
                st.session_state.culprit = story["culprit"]
            except json.JSONDecodeError:
                st.error("Failed to parse the story. Please try again.")

        
        if st.session_state.story:
            story = st.session_state.story
            st.write("**Setting:**", story["setting"])
            st.write("**Victim:**", story["victim"])
            st.write("**Suspects:**")
            for suspect, details in story["suspects"].items():
                st.write(f"- **{suspect}:** {details}")
            st.write("**Clues:**", ". ".join(story["clues"]))

            guess = st.text_input("Who do you think the culprit is?", value=st.session_state.input_value, key="guess")
            if st.button("Submit Guess"):
                if guess.lower() == st.session_state.culprit.lower():
                    st.success(f"Correct! The culprit was {st.session_state.culprit}.")
                    save_progress_sql(st.session_state.username, progress + 1)
                    st.success(story["explanation"])
                    st.success("Level completed! Progress saved.")
                    # Reset story for the next level
                    st.session_state.story = None
                    st.session_state.culprit = None
                else:
                    st.error("Incorrect guess! Try again.")