from flask import Flask, request, render_template_string, redirect, url_for
import subprocess, os, sys, json, argparse, time

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

# Common CSS style for templates
base_style = '''<style>
  body { font-family: system-ui, sans-serif; background: #f5f5f5; margin: 0; padding: 20px; }
  .container { max-width: 640px; margin: 40px auto; background: #fff; padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); border-radius: 8px; }
  h2 { margin-top: 0; }
  p.intro { font-size: 0.95rem; margin-bottom: 20px; }
  label { display: block; margin-bottom: 8px; font-weight: 500; }
  input { width: 100%; padding: 8px; margin: 4px 0 12px; border: 1px solid #ccc; border-radius: 4px; font-size: 1rem; }
  .btn { background-color: #f85e26; color: #fff; border: none; padding: 10px 20px; cursor: pointer; border-radius: 4px; font-size: 1rem; display: block; margin: 20px auto 0; }
  .btn:hover { opacity: 0.9; }
  pre { background: #f0f0f0; padding: 10px; border-radius: 4px; overflow-x: auto; }
  .footer { text-align: center; margin-top: 20px; font-size: 0.9rem; }
  .footer a { margin: 0 10px; color: #f85e26; text-decoration: none; }
  .footer a:hover { text-decoration: underline; }
</style>'''

# Footer HTML
footer_html = '''
<div class="footer">
  <a href="mailto:support@finmars.com" target="_blank">support@finmars.com</a> |
  <a href="https://docs.finmars.com/shelves/community-edition" target="_blank">Documentation</a> |
  <a href="https://github.com/finmars-platform/finmars-core/issues" target="_blank">Github</a>
</div>'''

# HTML templates
form_html = base_style + '''
<div class="container">
  <h2>Finmars Initial Setup</h2>
  <p class="intro">This short wizard will help you install Finmars on your server. Please provide the details below and click Continue Setup.</p>
  <form method="POST">
    <input type="hidden" name="step" value="generate_env">
    <label>Main Domain (e.g. finmars.example.com):<br><input name="DOMAIN" required></label>
    <label>Auth Domain (e.g. finmars-auth.example.com):<br><input name="AUTH_DOMAIN" required></label>
    <label>Admin Username:<br><input name="ADMIN_USERNAME" required></label>
    <label>Admin Password:<br><input name="ADMIN_PASSWORD" type="password" required></label>
    <button type="submit" class="btn">Continue Setup</button>
  </form>
  ''' + footer_html + '''
</div>
'''

step_button_html = base_style + '''
<div class="container">
  <h2>Finmars Setup: {{ label }}</h2>
  <form method="POST">
    <input type="hidden" name="step" value="{{ step }}">
    <button type="submit" class="btn">Continue Setup</button>
  </form>
  ''' + footer_html + '''
</div>
'''

status_html = base_style + '''
<div class="container">
  <h2>{{ title }}</h2>
  <pre>{{ logs }}</pre>
  <pre>Current status: {{ status }}</pre>
  ''' + footer_html + '''
</div>
'''

success_html = base_style + '''
<div class="container">
  <h2>✅ Setup Complete</h2>
  <p>You can now use the Finmars Platform.</p>
  ''' + footer_html + '''
</div>
'''

# State management
def default_state():
    state = { step: 'pending' for step, _, _ in get_setup_steps() }
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
        if stdout: logf.write(stdout)
        if stderr: logf.write(stderr)

# Autostart disable (systemd + cron)
def disable_autostart():
    try:
        subprocess.run(['systemctl', 'stop', 'init-setup'], check=False)
        subprocess.run(['systemctl', 'disable', 'init-setup'], check=False)
        unit_path = '/etc/systemd/system/init-setup.service'
        if os.path.exists(unit_path): os.remove(unit_path)
        subprocess.run(['systemctl', 'daemon-reload'], check=False)
    except Exception:
        pass
    try:
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

        if state.get(step) == 'requested':

            if step == 'init_cert':
                subprocess.run(['systemctl', 'stop', 'init-setup'], check=False)
                time.sleep(2)

            executed = True
            state[step] = 'in_progress'
            save_state(state)
            try:
                proc = subprocess.run(cmd, capture_output=True, text=True)
                append_log(title, proc.stdout, proc.stderr)
                state[step] = 'done' if proc.returncode == 0 else 'failed'
            except Exception as e:
                append_log(title, '', str(e))
                state[step] = 'failed'
            save_state(state)
            if step == 'init_cert': subprocess.run(['systemctl', 'start', 'init-setup'], check=False)
            if step == 'docker_up': disable_autostart()
            if os.path.exists(LOG_FILE):
                with open(LOG_FILE) as logf:
                    print(logf.read())
            sys.stdout.flush()
            break
    if not executed:
        print("[init-setup] No requested steps found, nothing to run.")
        sys.stdout.flush()

# Flask routes
@app.route('/', methods=['GET','POST'])
def setup():
    state = load_state()
    if request.method == 'POST':
        step = request.form.get('step')
        if step == 'generate_env' and state.get(step) == 'pending':
            inp = (
                f"{request.form['DOMAIN']}\n"
                f"{request.form['AUTH_DOMAIN']}\n"
                f"{request.form['ADMIN_USERNAME']}\n"
                f"{request.form['ADMIN_PASSWORD']}\n"
            )
            proc = subprocess.run(get_setup_steps()[0][1], input=inp, text=True, capture_output=True)
            append_log(get_setup_steps()[0][2], proc.stdout, proc.stderr)
            state['generate_env'] = 'done' if proc.returncode == 0 else 'failed'
            save_state(state)
            return redirect(url_for('setup'))
        if step in state and state[step] == 'pending':
            state[step] = 'requested'
            save_state(state)
        return redirect(url_for('setup'))
    logs = subprocess.run(['make', 'logs'], capture_output=True, text=True).stdout
    for step, _, title in get_setup_steps():
        status = state.get(step)
        if status == 'pending':
            if step == 'generate_env':
                return render_template_string(form_html)
            return render_template_string(step_button_html, step=step, label=title)
        if status in ('requested','in_progress'):
            return render_template_string(status_html, title=title, logs=logs, status=status)
    return success_html

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-step', action='store_true')
    args = parser.parse_args()
    if args.run_step:
        run_pending_step()
    else:
        if os.path.exists(LOG_FILE): os.remove(LOG_FILE)
        app.run(host='0.0.0.0', port=80)
