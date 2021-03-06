from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
 
shutdown_msg = ("The OpenCollar database has been disabled because of "
                "price increases from Google.  There is no update for the "
                "Owner Hud at this time.\n\n"
                "See the link below for more information.\n\n"
                "https://raw.github.com/nirea/ocupdater/master/docs/FAQ%20on%20OpenCollar%20Database%20Retirement.md")

class MainPage(webapp.RequestHandler):
    def get(self):
        self.response.set_status(404)
        self.response.out.write(shutdown_msg)

    def put(self):
        self.response.set_status(404)
        self.response.out.write(shutdown_msg)

    def delete(self):
        self.response.set_status(404)
        self.response.out.write(shutdown_msg)
                        
    def post(self):
        self.response.set_status(404)
        self.response.out.write(shutdown_msg)

            
application = webapp.WSGIApplication(
    [('.*', MainPage)
     ], 
    debug=True) 

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()
