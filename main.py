#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import os
import re
import webapp2
import jinja2
from google.appengine.ext import db
import hashlib

## Jinja Configuration
template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                               autoescape = True)
def render_str(template, **params):
    t = jinja_env.get_template(template)
    return t.render(params)

# Basic Handler class
class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

    def check_login(self):
        u = self.request.cookies.get("u_cookie")
        if u:
            u_list = u.split('|')
            u_hashed = hash_username(u_list[0])
            if u_hashed == u_list[1]:
                return u_list[0]
            else:
                return None              
        else:
            return None

    def login(self, username):
        u_cookie = write_usercookie(username)
        self.response.headers.add_header('Set-Cookie', "u_cookie=%s" % u_cookie)

    def logout(self):
        self.response.headers.add_header('Set-Cookie', "u_cookie=;Path=/")

class MainHandler(Handler):
    def get(self):
        self.render('front.html')

# Post Class    
class Post(db.Model):
    subject = db.StringProperty(required = True)
    content = db.TextProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)
    last_modified = db.DateTimeProperty(auto_now = True)
    author = db.StringProperty(required = True)
    content_html = db.TextProperty()
    short_description = db.StringProperty()

class NewPost(Handler):
    def get(self):
        username = self.check_login()
        if username:
            self.render("newpost.html", username=username)
        else:
            self.redirect("/login")

    def post(self):
        subject = self.request.get('subject')
        content = self.request.get('content')
        content_html = content.replace('\n', '<br>')
        username = self.check_login()
        if len(content) > 300:
            short_description = content[0:300] + "..."
        else:
            short_description = content

        if subject and content and username:
            p = Post(subject = subject, content = content, content_html=content_html, short_description=short_description, author=username)
            p.put()
            self.redirect('/post?key_id=%s' % str(p.key().id()) )
        else:
            error_subject = True
            if subject:
                error_subject = False
            error_content = True
            if content:
                error_content = False
            self.render("newpost.html", subject=subject, content=content, error_subject=error_subject, error_content=error_content)

class FrontPage(Handler):
    def get(self):
        posts = db.GqlQuery("select * from Post order by created desc limit 10")
        self.render('front.html', posts = posts)

class PostPage(Handler):
    def get(self):
        key_id = self.request.get("key_id")
        key = db.Key.from_path("Post", int(key_id))

        post = db.get(key)
        if not post:
            self.response.write("No post was found.")
            return
        else:
            q = "select * from Comment where post_key='%s' order by created desc limit 10" % key_id
            comments = db.GqlQuery(q)
            username = self.check_login()
            liked = False
            if username:
                query = "select * from Like where username = '%s' and post_key='%s'" % (username, str(post.key().id()))
                l = db.GqlQuery(query).get()
                if l:
                    liked = True
            self.render("post.html", post = post, liked = liked, comments = comments)

class EditPage(Handler):
    def get(self):
        username = self.check_login()
        if username:
            key_id = self.request.get("key_id")
            key = db.Key.from_path("Post", int(key_id))
            post = db.get(key)

            if not post:
                self.redirect("/front")
            else:
                if post.author == username:
                    self.render("edit.html", post=post, username=username)
        else:
            self.redirect("/login")

    def post(self):
        username = self.check_login()
        if username:
            key_id = self.request.get("key_id")
            key = db.Key.from_path("Post", int(key_id))
            post = db.get(key)

            if not post:
                self.redirect("/front")
            elif post.author == username:
                subject = self.request.get('subject')
                content = self.request.get('content')
                content_html = content.replace('\n', '<br>')
                if len(content) > 300:
                    short_description = content[0:300] + "..."
                else:
                    short_description = content
                if subject and content and username:
                    post.subject = subject
                    post.content = content
                    post.short_description = short_description
                    post.content_html = content_html
                    post.put()
                    self.redirect('/post?key_id=%s' % str(post.key().id()) )
                else:
                    error_subject = True
                    if subject:
                        error_subject = False
                    error_content = True
                    if content:
                        error_content = False
                    self.render("edit.html", subject=subject, content=content, error_subject=error_subject, error_content=error_content)
            else:
                self.redirect("/front")

        else:
            self.redirect("/login")

class Delete(Handler):
    def post(self):
        username = self.check_login()
        if username:
            key_id = self.request.get("key_id")
            key = db.Key.from_path("Post", int(key_id))
            post = db.get(key)

            if not post:
                self.redirect("/front")
            else:
                if post.author == username:
                    post.delete()
                    self.redirect("/front")
                else:
                    self.redirect("/front")

# User Stuff
class User(db.Model):
    username = db.StringProperty(required=True)
    passwordHashed = db.StringProperty(required=True)
    email = db.EmailProperty()

def hash_password(password):
    result = hashlib.sha256(password + "secretweaponry").hexdigest()
    return result

def hash_username(username):
    result = hashlib.sha256(username + "secretusersareprettyawesome").hexdigest()
    return result

def write_usercookie(username):
    u_hashed = hash_username(username)
    u_cookie = str(username + "|" + u_hashed)
    return u_cookie

class RegisterPage(Handler):
    def get(self):
        if self.check_login():
            self.redirect("/welcome")
        else:
            self.render('register.html')

    def post(self):
        username = self.request.get('username')
        email = self.request.get('email')
        password = self.request.get('password')
        confirm = self.request.get('confirm')
        query = "select * from User where username = '" + username + "'"
        u = db.GqlQuery(query).get()
        if u:
            self.render('register.html', username=username, email=email, error_username=True)
        elif password == confirm:
            p_hash = hash_password(password)
            if email:
                u = User(username=username, passwordHashed=p_hash, email=email)
                u.put()
            else: 
                u = User(username=username, passwordHashed=p_hash)
                u.put()
            self.login(username)
            self.redirect('/welcome')
        else:
            self.render('register.html', error_confirm=True, username=username, email=email)

class WelcomePage(Handler):
    def get(self):
        username = self.check_login()
        if username:
            self.render("welcome.html", username=username)
        else:
            self.redirect('/register')

class Logout(Handler):
    def post(self):
        self.logout()
        self.redirect("/register")

class LoginPage(Handler):
    def get(self):
        if self.check_login():
            self.redirect("/welcome")
        else:
            self.render("login.html")

    def post(self):
        username = self.request.get('username')
        password = self.request.get('password')
        query = "select * from User where username = '" + username + "'"
        u = db.GqlQuery(query).get()
        if u:
            p_hashed = hash_password(password)
            if p_hashed == u.passwordHashed:
                self.login(username)
                self.redirect("/welcome")
            else:
                self.render("login.html", error=True)
        else:            
            self.render("login.html", error=True)

class Like(db.Model):
    post_key = db.StringProperty(required = True)
    username = db.StringProperty(required = True)

class LikePage(Handler):
    def get(self):
        username = self.check_login()
        if username:
            key_id = self.request.get("key_id")
            key = db.Key.from_path("Post", int(key_id))
            post = db.get(key)

            if not post:
                self.redirect("/front")
            else:
                if post.author == username:
                    self.redirect("/front")
                else:
                    query = "select * from Like where username = '%s' and post_key='%s'" % (username, str(post.key().id()))
                    l = db.GqlQuery(query).get()
                    if l:
                        l.delete()
                    else:
                        like = Like(post_key= str(post.key().id()), username=username)
                        like.put()
                    self.redirect("/post?key_id=" + str(post.key().id()))

class Comment(db.Model):
    post_key = db.StringProperty(required = True)
    username = db.StringProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)
    content = db.StringProperty(required = True)

class CommentPage(Handler):
    def post(self):
        username = self.check_login()
        if username:
            key_id = self.request.get("key_id")
            key = db.Key.from_path("Post", int(key_id))
            post = db.get(key)

            if not post:
                self.redirect("/front")
            else:
                content = self.request.get("comment_content")
                comm = Comment(post_key=key_id, username=username, content=content)
                comm.put()
                self.redirect("/post?key_id="+key_id)

app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/newpost', NewPost),
    ('/post', PostPage),
    ('/front', FrontPage),
    ('/register', RegisterPage),
    ('/welcome', WelcomePage),
    ('/login', LoginPage),
    ('/logout', Logout),
    ('/edit', EditPage),
    ('/delete', Delete),
    ('/like', LikePage),
    ('/comment', CommentPage)
], debug=True)
