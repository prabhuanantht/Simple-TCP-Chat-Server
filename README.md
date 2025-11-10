# TCP Chat Server

A simple, multi-client TCP chat server built with Python's standard library. No external dependencies required!

## Features

- ✅ Multiple concurrent users (10+ simultaneous connections)
- ✅ Username-based login with collision detection
- ✅ Real-time message broadcasting
- ✅ Disconnect notifications
- ✅ List active users (`WHO` command)
- ✅ Direct messages (`DM` command)
- ✅ Idle timeout (60 seconds of inactivity)
- ✅ Heartbeat/ping support (`PING`/`PONG`)
- ✅ Configurable port via environment variable or command-line argument

## Requirements

- Python 3.6 or higher
- No external dependencies (uses only standard library)

## Installation

No installation needed! Just clone or download the repository.

```bash
git clone <your-repo-url>
cd chat-server-1
```

## Running the Server

### Default Port (4000)

```bash
python3 chat_server.py
```

### Custom Port via Command-Line Argument

```bash
python3 chat_server.py 5000
```

### Custom Port via Environment Variable

```bash
export CHAT_PORT=5000
python3 chat_server.py
```

The server will start and display:

```
[SERVER] Chat server started on 0.0.0.0:4000
[SERVER] Waiting for connections...
```

## Connecting to the Server

You can connect using `nc` (netcat), `telnet`, or any TCP client:

### Using netcat (recommended)

```bash
nc localhost 4000
```

### Using telnet

```bash
telnet localhost 4000
```

## Protocol Commands

### 1. Login (Required First)

```
LOGIN <username>
```

**Responses:**
- `OK` - Login successful
- `ERR username-taken` - Username already in use
- `ERR invalid-username` - Username is empty or invalid

### 2. Send Message

```
MSG <text>
```

Broadcasts your message to all connected users. They will see:

```
MSG <your-username> <text>
```

### 3. List Active Users

```
WHO
```

Returns a list of all connected users:

```
USER Alice
USER Bob
USER Charlie
```

### 4. Direct Message

```
DM <username> <text>
```

Sends a private message to a specific user. They will see:

```
DM <your-username> <text>
```

**Responses:**
- `ERR user-not-found` - Target user doesn't exist
- `ERR invalid-dm-format` - Invalid command format

### 5. Ping/Heartbeat

```
PING
```

**Response:**
```
PONG
```

## Example Usage

### Terminal 1 (User: Alice)

```bash
$ nc localhost 4000
LOGIN Alice
OK
MSG Hello everyone!
MSG How's everyone doing?
WHO
USER Alice
USER Bob
DM Bob Hey Bob, how are you?
```

### Terminal 2 (User: Bob)

```bash
$ nc localhost 4000
LOGIN Bob
OK
MSG Naman hi everyone!
MSG Hey Alice!
DM Alice I'm doing great, thanks!
```

### What Alice Sees

```
OK
MSG Bob Hey Alice!
DM Bob I'm doing great, thanks!
```

### What Bob Sees

```
OK
MSG Alice Hello everyone!
MSG Alice How's everyone doing?
USER Alice
USER Bob
DM Alice Hey Bob, how are you?
```

### When Bob Disconnects

Alice sees:

```
INFO Bob disconnected
```

## Complete Example Session

Here's a complete example with three users:

### User 1: Naman

```bash
$ nc localhost 4000
LOGIN Naman
OK
MSG hi everyone!
MSG Bob how are you?
WHO
USER Naman
USER Yudi
USER Charlie
INFO Charlie disconnected
```

### User 2: Yudi

```bash
$ nc localhost 4000
LOGIN Yudi
OK
MSG hello Naman!
MSG I'm doing great!
DM Naman Want to grab coffee later?
MSG Charlie just left!
```

### User 3: Charlie

```bash
$ nc localhost 4000
LOGIN Charlie
OK
MSG Hey folks!
MSG Sorry, gotta run!
^C  (disconnects)
```

## Error Handling

The server handles various error conditions:

1. **Username Already Taken**
   ```
   LOGIN Alice
   ERR username-taken
   ```

2. **Invalid Command**
   ```
   INVALID
   ERR unknown-command
   ```

3. **Must Login First**
   ```
   MSG Hello
   ERR must-login-first
   ```

4. **Idle Timeout** (60 seconds of inactivity)
   ```
   INFO idle-timeout
   (connection closed)
   ```

## Architecture

- **Threading Model**: Each client connection runs in its own thread
- **Thread-Safe**: Uses locks to protect shared data structures
- **Idle Timeout**: Background thread checks for inactive clients every 10 seconds
- **Graceful Shutdown**: Handles Ctrl+C to cleanly close all connections

## Stopping the Server

Press `Ctrl+C` in the server terminal:

```
^C
[SERVER] Shutting down...
[SERVER] Server stopped.
```

## Testing with Multiple Clients

Open multiple terminal windows and connect simultaneously:

**Terminal 1:**
```bash
nc localhost 4000
```

**Terminal 2:**
```bash
nc localhost 4000
```

**Terminal 3:**
```bash
nc localhost 4000
```

Each client can login with a different username and chat in real-time!

## Troubleshooting

### Port Already in Use

If you get an "Address already in use" error:

```bash
# Find the process using port 4000
lsof -i :4000

# Kill the process (replace PID with actual process ID)
kill -9 <PID>
```

Or use a different port:

```bash
python3 chat_server.py 5000
```

### Connection Refused

Make sure the server is running before connecting clients.

### Messages Not Appearing

- Ensure you've logged in first with `LOGIN <username>`
- Check that messages end with a newline (press Enter)
- Verify the server is still running

## Technical Details

- **Protocol**: Raw TCP sockets (no HTTP)
- **Encoding**: UTF-8
- **Message Delimiter**: Newline (`\n`)
- **Max Queued Connections**: 10
- **Idle Timeout**: 60 seconds
- **Timeout Check Interval**: 10 seconds

## License

This is a demonstration project. Feel free to use and modify as needed.

## Future Enhancements

Possible improvements for the future:

- Message history
- Chat rooms/channels
- Message encryption (TLS)
- User authentication with passwords
- Rate limiting
- Command history
- Rich text formatting
- File transfer support

