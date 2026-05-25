# SSH Configuration

The [ssh config](../meta/configs/ssh.yaml) links the following files:
* [ssh config](../ssh/config) to `~/.ssh/config`
* [ssh known_hosts_fixed](../ssh/known_hosts_fixed) to `~/.ssh/known_hosts_fixed`
    * Manually maintained known hosts.

The [ssh-authorized config](../meta/configs/ssh-authorized.yaml) links:
* [authorized_keys](../ssh/authorized_keys) to `~/.ssh/authorized_keys`
    * SSH keys permitted to connect to this machine.

The [ssh-known-hosts-ansible config](../meta/configs/ssh-known-hosts-ansible.yaml) links:
* [known_hosts_ansible](../ssh/known_hosts_ansible) to `~/.ssh/known_hosts_ansible`
    * Known hosts managed by Ansible and the [infrastructure repo](https://github.com/nstoik/infrastructure).

## WSL2: Bitwarden SSH Agent Bridge

On WSL2 hosts, the zshrc automatically bridges the Bitwarden Desktop SSH agent into WSL2 instead of using the omz `ssh-agent` plugin. This allows SSH keys managed in Bitwarden to be used from within WSL2.

### Prerequisites

1. **Bitwarden Desktop** must be installed on Windows with the SSH agent enabled:
   - Open Bitwarden Desktop → Settings → SSH Agent → enable "Enable SSH Agent"

2. **`socat`** must be installed in WSL2:
   ```bash
   sudo apt install socat
   ```

3. **`npiperelay.exe`** must be available on the Windows PATH:
   - Download from [jstarks/npiperelay](https://github.com/jstarks/npiperelay/releases)
   - Place `npiperelay.exe` in `C:\Windows\System32\`

### How it works

On WSL2, zshrc:
- Sets `SSH_AUTH_SOCK` to `~/.ssh/agent.sock`
- Starts a `socat` process (if not already running) that relays the Unix socket to the Windows named pipe `//./pipe/openssh-ssh-agent` used by Bitwarden Desktop
- Skips loading the omz `ssh-agent` plugin (which would conflict)

On non-WSL2 hosts, the omz `ssh-agent` plugin is loaded as normal.

### Testing the Bridge

After opening a new shell (or running `source ~/.zshrc`), verify the bridge is working:

**1. Check the socket exists and socat is running:**
```bash
ls -la ~/.ssh/agent.sock
pgrep -a socat
```

**2. Confirm `SSH_AUTH_SOCK` is set correctly:**
```bash
echo $SSH_AUTH_SOCK
# Expected: /home/<user>/.ssh/agent.sock
```

**3. List keys loaded in Bitwarden's SSH agent:**
```bash
ssh-add -l
```
Expected output: one or more key fingerprints. If you see `The agent has no identities.`, Bitwarden has no SSH keys added. If you see `Error connecting to agent`, the bridge is not working — check that Bitwarden Desktop is running and the SSH agent is enabled.

**4. Test an actual SSH connection** (replace `git@github.com` with any host you have a key for):
```bash
ssh -T git@github.com
# Expected: "Hi <username>! You've successfully authenticated..."
```

### Troubleshooting

- If `ssh-add -l` fails, restart the bridge manually:
  ```bash
  rm -f ~/.ssh/agent.sock
  source ~/.zshrc
  ssh-add -l
  ```
- Ensure Bitwarden Desktop is unlocked and `npiperelay.exe` is on the Windows PATH.
- Verify the named pipe exists from WSL2: `ls /mnt/c/Windows/System32/npiperelay.exe`
