import webview
from threading import Thread
from time import sleep

# this is used to allow js to access python code
class JS_API:
    def do_thing():
        print('suh')

window = webview.create_window('CHIP-8 Emulator', 'index.html', js_api=JS_API)



#def testing_eval_js(message:str):
#    print('starting')
#    sleep(5)
#    print('should happen now!')
#    window.evaluate_js(rf"""
#        const sidebarH1 = document.querySelector(".sidebar > h1");
#        sidebarH1.innerHTML = "{message}";
#    """)
#
#Thread(target=testing_eval_js, args=('thing instead!',), daemon=True).start()

webview.start()