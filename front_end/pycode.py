
import webview

# this is used to allow js to access python code
class JS_API:
    def do_thing():
        print('suh')

window = webview.create_window('Testing front end stuff!', 'index.html', js_api=JS_API)
webview.start()

"""
app_name = "edomode"

class Api():
    def do_a_flip(self, message):
        print(message)
    def print_in_terminal(self, message):
        print(message)

if __name__ == '__main__':
    api = Api()
    webview.create_window(app_name, url='edomode_A0.02_index.html', js_api=api, min_size=(600, 450))
    webview.start()
"""
#---------------
