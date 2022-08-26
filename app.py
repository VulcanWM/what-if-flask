from flask import Flask, render_template, request, redirect
from functions import get_user, add_user, get_nv_scenario_user, add_scenario, url_encode, accept_scenario, decline_scenario, get_all_nvs, get_max_id, get_all_scenarios, get_scenario, get_all_comments, post_comment, edit_scenario, delete_comment, ban_user, unban_user, add_warning, get_user_from_username, if_user_follows
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")


@app.route('/')
def index():
  if request.headers['X-Replit-User-Id']:
    return redirect("/dashboard")
  else:
    return render_template("index.html")

@app.route('/dashboard')
def dashboard():
    user_id = request.headers['X-Replit-User-Id']
    user_name=request.headers['X-Replit-User-Name']
    if user_id:
      msg = request.args.get("msg", False)
      if get_user(user_id) == False:
        add_user(user_id, user_name)
        return redirect("/intro")
      else:
        document = get_user(user_id)
        if document.get("Banned", False) != False:
          return render_template("banned.html", document=document)
        sort = request.args.get("sort", "All")
        return render_template(
          'dashboard.html',
          user_id=user_id,
          user_name=user_name,
          document=document,
          max_id=get_max_id(),
          scenarios=get_all_scenarios(),
          sort=sort,
          text=msg
        )
    else:
      return redirect("/login")
      
@app.route("/login")
def login():
  if request.headers['X-Replit-User-Id']:
    return redirect("/dashboard")
  else:
    return render_template("login.html")

@app.route("/intro")
def intro():
  if request.headers['X-Replit-User-Id']:
    return redirect("/intro/1")
  else:
    return redirect("/")

@app.route("/intro/1")
def intro1():
  if request.headers['X-Replit-User-Id']:
    return render_template("intro.html", slide=1)
  else:
    return redirect("/")

@app.route("/intro/2")
def intro2():
  if request.headers['X-Replit-User-Id']:
    return render_template("intro.html", slide=2)
  else:
    return redirect("/")

@app.route("/intro/3")
def intro3():
  if request.headers['X-Replit-User-Id']:
    return render_template("intro.html", slide=3)
  else:
    return redirect("/")

@app.route("/newscenario")
def newscenariopage():
  if request.headers['X-Replit-User-Id']:
    if get_user(request.headers['X-Replit-User-Id']).get("Banned", False) == True:
      return redirect("/dashboard")
    return render_template("newscenario.html", document=get_user(request.headers['X-Replit-User-Id']))
  else:
    return redirect("/")

@app.route("/newscenario", methods=['POST', 'GET'])
def newscenariofunc():
  if request.method == 'POST':
    user_id = request.headers['X-Replit-User-Id']
    if get_user(request.headers['X-Replit-User-Id']).get("Banned", False) == True:
      return redirect("/dashboard")
    if user_id:
      if len(get_nv_scenario_user(user_id)) > 5:
        return redirect(f"/dashboard?msg={url_encode('You cannot have more than 5 unverified scenarios!')}")
      title = request.form['title']
      desc = request.form['desc']
      func = add_scenario(title, desc, user_id)
      return redirect(f"/dashboard?msg={url_encode(func)}")
    else:
      return redirect("/")
  else:
    return redirect("/newscenario")

@app.route("/admin")
def admin_page():
  user_id = request.headers['X-Replit-User-Id']
  if user_id:
    if get_user(user_id) == False:
      return redirect("/")
    else:
      if get_user(request.headers['X-Replit-User-Id']).get("Banned", False) == True:
        return redirect("/dashboard")
      if "Moderator" in get_user(user_id)['Roles']:
        msg = request.args.get("msg", "")
        return render_template("admin.html", msg=msg, scenarios=get_all_nvs())        
      else:
        return redirect(f"/dashboard?msg={url_encode('You are not a moderator!')}")
  else:
    return redirect("/")

@app.route("/accept_scenario/<theid>")
def accept_scenario_page(theid):
  user_id = request.headers['X-Replit-User-Id']
  if user_id:
    if get_user(user_id) == False:
      return redirect("/")
    else:
      if get_user(request.headers['X-Replit-User-Id']).get("Banned", False) == True:
        return redirect("/dashboard")
      if "Moderator" in get_user(user_id)['Roles']:
        func = accept_scenario(theid)
        return redirect(f"/admin?msg={url_encode(func)}")
      else:
        return redirect(f"/dashboard?msg={url_encode('You are not a moderator!')}")
  else:
    return redirect("/")

@app.route("/decline_scenario/<theid>")
def decline_scenario_page(theid):
  user_id = request.headers['X-Replit-User-Id']
  if user_id:
    if get_user(user_id) == False:
      return redirect("/")
    else:
      if get_user(request.headers['X-Replit-User-Id']).get("Banned", False) == True:
        return redirect("/dashboard")
      if "Moderator" in get_user(user_id)['Roles']:
        func = decline_scenario(theid)
        return redirect(f"/admin?msg={url_encode(func)}")
      else:
        return redirect(f"/dashboard?msg={url_encode('You are not a moderator!')}")
  else:
    return redirect("/")

@app.route("/scenario/<theid>")
def scenario_page(theid):
  user_id = request.headers['X-Replit-User-Id']
  if user_id:
    if get_user(request.headers['X-Replit-User-Id']).get("Banned", False) == True:
      return redirect("/dashboard")
    scenario = get_scenario(theid)
    if scenario == False:
      return redirect(f"/dashboard?msg={url_encode('That was not a real scenario!')}")
    user = get_user(user_id)
    comments = get_all_comments(theid)
    return render_template("scenario.html", scenario=scenario, user=user, comments=comments)

@app.route("/postcomment/<theid>", methods=['POST', 'GET'])
def post_comment_page(theid):
  if request.method == 'POST':
    user_id = request.headers['X-Replit-User-Id']
    user_name=request.headers['X-Replit-User-Name']
    if user_id:
      if get_user(request.headers['X-Replit-User-Id']).get("Banned", False) == True:
        return redirect("/dashboard")
      comment = request.form['comment']
      post_func = post_comment(theid, comment, user_id, user_name)
      if post_func == True:
        return redirect(f"/scenario/{theid}")
      else:
        return redirect(f"/dashboard?msg={url_encode(post_func)}")
    else:
      return redirect("/login")
  else:
    return redirect(f"/scenario/{theid}")

@app.route("/editscenario/<theid>")
def edit_scenario_page(theid):
  user_id = request.headers['X-Replit-User-Id']
  if user_id:
    if get_user(request.headers['X-Replit-User-Id']).get("Banned", False) == True:
      return redirect("/dashboard")
    if "Moderator" in get_user(user_id)['Roles']:
      if get_scenario(theid) == False:
        return redirect(f"/admin?msg={url_encode('That is not a real scenario!')}")
      else:
        return render_template("editscenario.html", scenario=get_scenario(theid))
    else:
      return redirect(f"/dashboard?{url_encode('You are not a moderator!')}")
  else:
    return redirect("/login")

@app.route("/editscenario/<theid>", methods=['POST', 'GET'])
def edit_scenario_func(theid):
  if request.method == 'POST':
    user_id = request.headers['X-Replit-User-Id']
    if user_id:
      if get_user(request.headers['X-Replit-User-Id']).get("Banned", False) == True:
        return redirect("/dashboard")
      if "Moderator" in get_user(user_id)['Roles']:
        title = request.form['title']
        desc = request.form['desc']
        func = edit_scenario(theid, title, desc)
        if func == True:
          return redirect(f"/scenario/{theid}")
        else:
          return redirect(f"/admin?msg={url_encode(func)}")
      else:
        return redirect(f"/dashboard?{url_encode('You are not a moderator!')}")
    else:
      return redirect("/login")
  else:
    return redirect(f"/editscenario/{theid}")

@app.route("/deletecomment/<postid>/<username>")
def delete_scenario_page(postid, username):
  user_id = request.headers['X-Replit-User-Id']
  if user_id:
    if get_user(request.headers['X-Replit-User-Id']).get("Banned", False) == True:
      return redirect("/dashboard")
    if "Moderator" in get_user(user_id)['Roles']:
      func = delete_comment(username, postid)
      if func == True:
        return redirect(f"/scenario/{postid}")
      else:
        return redirect(f"/admin?msg={url_encode(func)}")
    else:
      return redirect(f"/dashboard?{url_encode('You are not a moderator!')}")
  else:
    return redirect("/login")

@app.route("/banuser", methods=['POST', 'GET'])
def ban_user_page():
  if request.method == 'POST':
    user_id = request.headers['X-Replit-User-Id']
    if user_id:
      if get_user(request.headers['X-Replit-User-Id']).get("Banned", False) == True:
        return redirect("/dashboard")
      if "Moderator" in get_user(user_id)['Roles']:
        username = request.form['username']
        reason = request.form['reason']
        func = ban_user(username, reason)
        if func == True:
          return redirect(f"/admin?msg={url_encode(f'{username} is banned!')}")
        else:
          return redirect(f"/admin?msg={func}")
      else:
        return redirect(f"/dashboard?{url_encode('You are not a moderator!')}")
    else:
      return redirect("/login")
  else:
    return redirect("/admin")

@app.route("/unbanuser", methods=['POST', 'GET'])
def unban_user_page():
  if request.method == 'POST':
    user_id = request.headers['X-Replit-User-Id']
    if user_id:
      if get_user(request.headers['X-Replit-User-Id']).get("Banned", False) == True:
        return redirect("/dashboard")
      if "Moderator" in get_user(user_id)['Roles']:
        username = request.form['username']
        func = unban_user(username)
        if func == True:
          return redirect(f"/admin?msg={url_encode(f'{username} is unbanned!')}")
        else:
          return redirect(f"/admin?msg={func}")
      else:
        return redirect(f"/dashboard?{url_encode('You are not a moderator!')}")
    else:
      return redirect("/login")
  else:
    return redirect("/admin")

@app.route("/addwarning", methods=['POST', 'GET'])
def add_warning_page():
  if request.method == 'POST':
    user_id = request.headers['X-Replit-User-Id']
    if user_id:
      if get_user(request.headers['X-Replit-User-Id']).get("Banned", False) == True:
        return redirect("/dashboard")
      if "Moderator" in get_user(user_id)['Roles']:
        username = request.form['username']
        amount = request.form['amount']
        func = add_warning(username, amount)
        if func == True:
          return redirect(f"/admin?msg={url_encode(f'{username}s warnings have been altered!')}")
        else:
          return redirect(f"/admin?msg={func}")
      else:
        return redirect(f"/dashboard?{url_encode('You are not a moderator!')}")
    else:
      return redirect("/login")
  else:
    return redirect("/admin")

@app.route("/usernamefromid")
def usernamefromid():
  user_id = request.headers['X-Replit-User-Id']
  if user_id:
    return render_template("usernamefromid.html", document=get_user(user_id))
  else:
    return render_template("usernamefromid.html", document={"Roles": []})

@app.route("/usernamefromid", methods=['POST', 'GET'])
def usernamefromidfunc():
  if request.method == 'POST':
    your_id = request.headers['X-Replit-User-Id']
    if your_id:
      document = get_user(your_id)
    else:
      document = {"Roles": []}
    userid = request.form['id']
    user = get_user(int(userid))
    if user == False:
      return render_template("usernamefromid.html", msg=f"{userid} is not a real Replit userid!", document=document)
    else:
      return render_template("usernamefromid.html", msg=f"{userid} is {user['Username']}'s userid!", document=document)
  else:
    return redirect("/usernamefromid")

@app.route("/profile")
def profile():
  user_name = request.headers['X-Replit-User-Name']
  if user_name:
    return redirect(f"/user/{user_name}")
  else:
    return redirect("/login")

@app.route("/user/<username>")
def user_page(username):
  user_id = request.headers['X-Replit-User-Id']
  if user_id:
    if get_user_from_username(username) == False:
      return redirect(f"/dashboard?msg={username} is not a real user")
    if get_user_from_username(username).get("Banned", False) != False:
      return redirect(f"/dashboard?msg={username} is banned!")
    return render_template("userprofile.html", document=get_user_from_username(username), user=get_user(user_id), max_id=get_max_id(), scenarios=get_all_scenarios(), rolesinfo={"Owner": "This user is the owner of this website!", "Moderator": "This User has the power to do anything!", "Helper": "This user has suggested a scenario and it has been verified!", "Tester": "This user has helped in testing out this website!", "Contributor": "This user has helped with this website's code!", "Supporter": "This user follows VulcanWM"}, follows=if_user_follows(username))
  else:
    return redirect("/login")