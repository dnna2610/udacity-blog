# Blog
This is a simple blog application that allows users to write, edit, delete their posts and like other people's posts.

# Directories of all pages:
- '/front' - Front Blog Page - List 10 most recent blog posts
- '/welcome' - Welcome Page - Welcome the user afer he/she signs in or registers
- '/newpost' - Write new blog post
- '/post' - Page to view individual post (needs a post key) - User can like or delete a post here
- '/register' - Page for new user to register
- '/login' - Login page
- '/edit' - Page to edit individual post (needs a post key and the user have to be the orginal author)
- '/edit_comment' - Page to edit the comment (also need to be logged in and the user that post the comment)

# Link
The blog is currently running at: http://blog-145310.appspot.com/

# Instructions
To run the project, add this application in Google App Engine and run it. The application would then be running
on local host. To deploy this app on appspot, delete the application and version properties in the file
app.yaml and run command: `gcloud app deploy`