from flask import Flask, request, render_template_string, redirect, url_for
import subprocess, os, sys, json, argparse

app = Flask(__name__)

STATE_FILE = '.init-setup-state.json'
LOG_FILE = 'init-setup-log.txt'

# Define steps and associated commands and titles
def get_setup_steps():
    return [
        ('generate_env', ['make', 'generate-env'], '.env Created'),
        ('init_cert', ['make', 'init-cert'], 'Certificates Initialized'),
        ('init_keycloak', ['make', 'init-keycloak'], 'Keycloak Initialized'),
        ('migrate', ['make', 'migrate'], 'Database Migrated'),
        ('docker_up', ['make', 'up'], 'Services Started')
    ]

# HTML templates
form_html = '''
<h2>Finmars Initial Setup</h2>
<form method="POST">
  <input type="hidden" name="step" value="generate_env">
  Main Domain (e.g. ap.finmars.com): <input name="DOMAIN" required><br>
  Auth Domain (e.g. auth.ap-finmars-auth.finmars.com): <input name="AUTH_DOMAIN" required><br>
  Admin Username: <input name="ADMIN_USERNAME" required><br>
  Admin Password: <input name="ADMIN_PASSWORD" type="password" required><br>
  <button type="submit">Create .env Now</button>
</form>
'''

step_button_html = '''
<h2>Finmars Setup: {{ label }}</h2>
<form method="POST">
  <input type="hidden" name="step" value="{{ step }}">
  <button type="submit">Request {{ label }}</button>
</form>
'''

status_html = '''
<h2>{{ title }}</h2>
<pre>{{ logs }}</pre>
<pre>Current status: {{ status }}</pre>
<script>
  setTimeout(function() { window.location.reload(); }, 5000);
</script>
'''

success_html = '''
<h2>✅ Setup Complete</h2>
<p>You can now use the Finmars Platform.</p>
'''

# State management

def default_state():
    state = {}
    for step, _, _ in get_setup_steps():
        state[step] = 'pending'
    save_state(state)
    return state


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return default_state()


def save_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

# Logging helper

def append_log(title, stdout, stderr):
    with open(LOG_FILE, 'a') as logf:
        logf.write(f"\n\n### {title}\n")
        if stdout:
            logf.write(stdout)
        if stderr:
            logf.write(stderr)

# Autostart disable (systemd + cron)
def disable_autostart():
    try:
        # Stop and disable the systemd service
        subprocess.run(['systemctl', 'stop', 'init-setup'], check=False)
        subprocess.run(['systemctl', 'disable', 'init-setup'], check=False)
        unit_path = '/etc/systemd/system/init-setup.service'
        if os.path.exists(unit_path):
            os.remove(unit_path)
        subprocess.run(['systemctl', 'daemon-reload'], check=False)
    except Exception:
        pass
    try:
        # Remove cron job entry
        subprocess.run("(crontab -l | grep -v 'init-setup.py --run-step') | crontab -", shell=True, check=False)
    except Exception:
        pass

# Runner: background run one pending requested step

def run_pending_step():
    state = load_state()
    print("[init-setup] Loaded state:", state)
    sys.stdout.flush()
    executed = False
    for step, cmd, title in get_setup_steps():
        # If initializing certs, stop the web server to free port 80
        if step == 'init_cert':
            print("[init-setup] Stopping init-setup service to free port 80...")
            sys.stdout.flush()
            subprocess.run(['systemctl', 'stop', 'init-setup'], check=False)
            # Brief pause to ensure port is released
            time.sleep(2)

        if state.get(step) == 'requested':
            executed = True
            print(f"[init-setup] Executing step: {step}")
            sys.stdout.flush()
            state[step] = 'in_progress'
            save_state(state)
            try:
                proc = subprocess.run(cmd, capture_output=True, text=True)
                append_log(title, proc.stdout, proc.stderr)
                new_status = 'done' if proc.returncode == 0 else 'failed'
                state[step] = new_status
                print(f"[init-setup] Step {step} completed with status {new_status}")
            except Exception as e:
                append_log(title, '', str(e))
                state[step] = 'failed'
                print(f"[init-setup] Step {step} failed with exception: {e}")
            save_state(state)
            # After docker_up, disable init-setup service
            if step == 'docker_up':
                print("[init-setup] Disabling init-setup autostart...")
                disable_autostart()
            # print log file to console
            if os.path.exists(LOG_FILE):
                with open(LOG_FILE) as logf:
                    print(logf.read())
            sys.stdout.flush()
            break
    if not executed:
        print("[init-setup] No requested steps found, nothing to run.")
        sys.stdout.flush()

# Flask routes
@app.route('/', methods=['GET', 'POST'])
def setup():
    state = load_state()
    if request.method == 'POST':
        step = request.form.get('step')
        # Handle generate_env synchronously
        if step == 'generate_env' and state.get(step) == 'pending':
            inp = (
                f"y\n{request.form['DOMAIN']}\n"
                f"{request.form['AUTH_DOMAIN']}\n"
                f"{request.form['ADMIN_USERNAME']}\n"
                f"{request.form['ADMIN_PASSWORD']}\n"
            )
            cmd = ['make', 'generate-env']
            print(f"[init-setup] Running generate-env with input:\n{inp}")
            sys.stdout.flush()
            proc = subprocess.run(cmd, input=inp, text=True, capture_output=True)
            append_log('.env Created', proc.stdout, proc.stderr)
            status = 'done' if proc.returncode == 0 else 'failed'
            state['generate_env'] = status
            save_state(state)
            return redirect(url_for('setup'))
        # Queue other steps
        if step in state and state[step] == 'pending':
            state[step] = 'requested'
            save_state(state)
        return redirect(url_for('setup'))

    # GET flow: determine UI
    logs = open(LOG_FILE).read() if os.path.exists(LOG_FILE) else ''
    for step, _, title in get_setup_steps():
        status = state.get(step)
        if status == 'pending':
            if step == 'generate_env':
                return render_template_string(form_html)
            return render_template_string(step_button_html, step=step, label=title)
        if status in ('requested', 'in_progress'):
            return render_template_string(status_html, title=title, logs=logs, status=status)
    # all done
    return success_html

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-step', action='store_true')
    args = parser.parse_args()
    if args.run_step:
        run_pending_step()
    else:
        # clear logs at start
        if os.path.exists(LOG_FILE): os.remove(LOG_FILE)
        app.run(host='0.0.0.0', port=80)
