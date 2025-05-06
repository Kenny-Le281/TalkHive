from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import join_room, leave_room, send, SocketIO
import random
from string import ascii_uppercase

# Initialize Flask App
app = Flask(__name__)  # Create a new Flask web application
app.config["SECRET_KEY"] = "hjhjsdahhds"
socketio = SocketIO(app) # Initialize Flask-SocketIO to handle WebSocket communication

# Dictionary to store rooms and their member count and messages
# Here these are examples of predetermined rooms initally with no memebers and no messages
rooms = {
    "SPORTS": {"members": 0, "messages": []},
    "BUSINESS": {"members": 0, "messages": []},
    "TECHNOLOGY": {"members": 0, "messages": []},
    "MUSIC": {"members": 0, "messages": []},
    "ART": {"members": 0, "messages": []}
}

# Generating a unique code room
def generate_unique_code(length):
    while True:
        code = ""
        for i in range(length):
            code += random.choice(ascii_uppercase) # Generating random code
        
        # Ensure the code is unique and not already used as a room code
        if code not in rooms:
            break
    
    return code

# Route for the home page where users can join or create a room
@app.route("/", methods=["POST", "GET"])
def home():
    session.clear()
    if request.method == "POST":
        name = request.form.get("name")
        code = request.form.get("code")
        predefined_room = request.form.get("predefined-room")
        create = request.form.get("create", False)

        # Validate user input

        if not name:
            return render_template("home.html", error="Please enter a name.", code=code, predefined_room=predefined_room, name=name)

        if not (code or predefined_room):
            return render_template("home.html", error="Please enter a room code or select a predefined room.", code=code, predefined_room=predefined_room, name=name)
        
        room = predefined_room or code
        if create:
            room = generate_unique_code(4)
            rooms[room] = {"members": 0, "messages": []}
        elif room not in rooms:
            return render_template("home.html", error="Room does not exist.", code=code, predefined_room=predefined_room, name=name)
        
        session["room"] = room
        session["name"] = name
        return redirect(url_for("room")) # Redirect the user to the room page

    return render_template("home.html")



# Route for the room page where users can chat in real-time
@app.route("/room")
def room():
    room = session.get("room")
    if room is None or session.get("name") is None or room not in rooms:
        return redirect(url_for("home"))

    # Render the room page with the room code and messages history
    return render_template("room.html", code=room, messages=rooms[room]["messages"])

@socketio.on("message")
def message(data):
    room = session.get("room")
    if room not in rooms:
        return None
    
    # Create a message object with the sender's name and message content
    content = {
        "name": session.get("name"),
        "message": data["data"]
    }
    send(content, to=room) # Send the message to all users in the room via WebSocket
    rooms[room]["messages"].append(content) # Store the message in the room's message history
    print(f"{session.get('name')} said: {data['data']}") # Print the messafe to the console

@socketio.on("connect")
def connect(auth):
    room = session.get("room")
    name = session.get("name")
    if not room or not name:
        return
    if room not in rooms:
        leave_room(room)
        return
    
    join_room(room)
    send({"name": name, "message": "has entered the room"}, to=room)
    rooms[room]["members"] += 1
    print(f"{name} joined room {room}")

@socketio.on("disconnect")
def disconnect():
    room = session.get("room")
    name = session.get("name")
    leave_room(room)

    if room in rooms:
        rooms[room]["members"] -= 1
        if rooms[room]["members"] <= 0:
            del rooms[room]
    
    send({"name": name, "message": "has left the room"}, to=room)
    print(f"{name} has left the room {room}")

if __name__ == "__main__":
    socketio.run(app, debug=True)
