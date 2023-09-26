import tkinter as tk
from tkinter import messagebox, Frame, Scrollbar
from bs4 import BeautifulSoup
from selenium import webdriver
from PIL import Image, ImageTk
from io import BytesIO
import requests, threading, time, random, json, os, queue
from plyer import notification
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import simpleaudio as sa
from config import USER_AGENTS

class YouTubeNotifier(tk.Tk):
    LAST_VIDEO_URLS = {}
    initial_check = {}
    def __init__(self):
        super().__init__()

        self.queue = queue.Queue()

        self.title("Pigeon Peck")
        self.geometry("1000x600")
        self.setup_widgets()
        self.center_window()
        self.load_from_json()
        for channel_name_with_handle, channel_info in self.LAST_VIDEO_URLS.items():
            self.subscribed_channels_listbox.insert(tk.END, channel_name_with_handle)
        self.start_video_checker()

    def start_video_checker(self):
        # Start a new thread for checking new videos
        self.checker_thread = threading.Thread(target=self.check_new_videos_periodically)
        self.checker_thread.daemon = True  # Daemon thread will stop when the main program exits.
        self.checker_thread.start()

    def check_new_videos_periodically(self):
        while True:
            self.check_new_videos()
            time.sleep(10)

    def save_to_json(self):
        with open('saved_channels.json', 'w') as f:
            json.dump(self.LAST_VIDEO_URLS, f, indent=4)

    def load_from_json(self):
        if os.path.exists('saved_channels.json'):
            with open('saved_channels.json', 'r') as f:
                self.LAST_VIDEO_URLS = json.load(f)
                print("Loaded LAST_VIDEO_URLS:", self.LAST_VIDEO_URLS)
                for handle in self.LAST_VIDEO_URLS:
                    self.initial_check[handle] = False
        else:
            self.LAST_VIDEO_URLS = {}

    def check_new_videos(self):
        for channel_name_with_handle in self.subscribed_channels_listbox.get(0, tk.END):
            try:
                handle = channel_name_with_handle.split('(')[-1].replace(')', '').strip()
                current_video_urls = self.get_latest_video_urls(handle)

                stored_data = self.LAST_VIDEO_URLS.get(handle, {})
                stored_videos = stored_data.get("videos", [])
                stored_shorts = stored_data.get("shorts", [])
                if isinstance(stored_videos, str):
                    stored_videos = [stored_videos]
                if isinstance(stored_shorts, str):
                    stored_shorts = [stored_shorts]

                current_videos = current_video_urls[0] if len(current_video_urls) > 0 else None
                current_shorts = current_video_urls[1] if len(current_video_urls) > 1 else None

                if handle not in self.initial_check:
                    self.initial_check[handle] = True

                if self.initial_check[handle]:
                    if current_videos and current_videos not in stored_videos:
                        stored_videos.append(current_videos)
                    if current_shorts and current_shorts not in stored_shorts:
                        stored_shorts.append(current_shorts)

                    self.LAST_VIDEO_URLS[handle] = {
                        "videos": stored_videos,
                        "shorts": stored_shorts
                    }
                    self.save_to_json()
                    self.initial_check[handle] = False
                    continue

                new_video_detected = False

                if current_videos and current_videos not in stored_videos:
                    stored_videos.append(current_videos)
                    new_video_detected = True

                if current_shorts and current_shorts not in stored_shorts:
                    stored_shorts.append(current_shorts)
                    new_video_detected = True

                if new_video_detected:
                    print(f"New Video Detected for {channel_name_with_handle}")
                    notification.notify(
                        title="New Video Detected!",
                        message=f"{channel_name_with_handle} has uploaded a new video!",
                        timeout=3
                    )
                    self.play_sound('assets/sounds/notify.wav')
                    self.queue.put(("new_video", channel_name_with_handle))
                    self.LAST_VIDEO_URLS[handle] = {
                        "videos": stored_videos,
                        "shorts": stored_shorts
                    }
                    self.save_to_json()
                    print("JSON Updated")

            except Exception as e:
                print(f"Error checking for {channel_name_with_handle}: {e}")

    def get_latest_video_urls(self, handle):

        options = webdriver.FirefoxOptions()
        options.add_argument('--headless')
        options.set_preference("general.useragent.override", random.choice(USER_AGENTS))
        browser = webdriver.Firefox(options=options)

        videos_and_shorts = {
            "videos": "ytd-rich-grid-row.style-scope:nth-child(1) > div:nth-child(1) > ytd-rich-item-renderer:nth-child(1) > div:nth-child(1) > ytd-rich-grid-media:nth-child(1) > div:nth-child(1) > div:nth-child(1) > ytd-thumbnail:nth-child(1) > a:nth-child(1)",
            "shorts": "ytd-rich-grid-row.style-scope:nth-child(1) > div:nth-child(1) > ytd-rich-item-renderer:nth-child(1) > div:nth-child(1) > ytd-rich-grid-slim-media:nth-child(1) > div:nth-child(1) > ytd-thumbnail:nth-child(1) > a:nth-child(1)"
        }

        found_links = []

        for vids, selector in videos_and_shorts.items():
            browser.get(f'https://www.youtube.com/{handle}/{vids}')

            try:
                element_present = EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                WebDriverWait(browser, 10).until(element_present)

                soup = BeautifulSoup(browser.page_source, 'html.parser')
                video_anchor = soup.select_one(selector)

                if video_anchor and 'href' in video_anchor.attrs:
                    found_links.append('https://www.youtube.com' + video_anchor['href'])
                    print(
                        f"Found link for {vids}: {'https://www.youtube.com' + video_anchor['href'] if video_anchor else 'Not found'}")

            except Exception as e:
                print(f"Error finding {vids} for {handle}: {e}")

        browser.quit()
        return found_links

    def setup_widgets(self):
        # Search bar
        self.search_var = tk.StringVar()
        entry = tk.Entry(self, textvariable=self.search_var)
        entry.grid(row=0, column=0, columnspan=3, pady=10, padx=10, sticky='ew')
        entry.bind('<Return>', lambda event=None: self.search())
        tk.Button(self, text="Search", command=self.search).grid(row=0, column=3, pady=10, padx=10)

        # Subscribed channels list on the left
        tk.Label(self, text="Subscribed Channels").grid(row=1, column=0, padx=10, sticky='w')
        self.subscribed_channels_listbox = tk.Listbox(self)
        self.subscribed_channels_listbox.grid(row=2, column=0, rowspan=2, padx=10, sticky='nsew')
        tk.Button(self, text="Remove from list", command=self.delete_channel).grid(row=4, column=0, padx=10,
                                                                                            pady=5, sticky='ew')

        # Configure row and column weights for resizing
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # Search results on the right
        tk.Label(self, text="Search Results").grid(row=1, column=1, columnspan=2, padx=10, sticky='w')

        # Scrollable frame for results
        self.results_canvas = tk.Canvas(self, bd=0, highlightthickness=0, takefocus=1)
        self.results_canvas.bind("<Enter>", lambda e: self.recursive_bind_mousewheel(self.results_canvas))
        self.results_canvas.bind("<Leave>", lambda e: self.results_canvas.unbind("<MouseWheel>"))
        self.results_canvas.grid(row=2, column=1, columnspan=2, sticky="nsew")
        self.results_scrollbar = Scrollbar(self, orient="vertical", command=self.results_canvas.yview)
        self.results_scrollbar.grid(row=2, column=3, sticky="ns")
        self.results_canvas.configure(yscrollcommand=self.results_scrollbar.set)

        self.results_inner_frame = Frame(self.results_canvas)
        self.results_canvas.create_window((0, 0), window=self.results_inner_frame, anchor="nw")

        self.results_inner_frame.bind("<Configure>", lambda e: self.results_canvas.configure(
            scrollregion=self.results_canvas.bbox("all")))

    def _on_mousewheel(self, event):
        if self.tk.call('tk', 'windowingsystem') == 'aqua': # macOS
            delta = -event.delta
        else:
            delta = event.delta // 120

        self.results_canvas.yview_scroll(delta, "units")

    def recursive_bind_mousewheel(self, widget):
        widget.bind("<MouseWheel>", self._on_mousewheel)
        for child in widget.winfo_children():
            self.recursive_bind_mousewheel(child)

    def play_sound(self, filename):
        wave_obj = sa.WaveObject.from_wave_file(filename)
        play_obj = wave_obj.play()
        play_obj.wait_done()

    def center_window(self):
        self.update_idletasks()
        w = self.winfo_screenwidth()
        h = self.winfo_screenheight()
        size = tuple(int(_) for _ in self.geometry().split('+')[0].split('x'))
        x = w / 2 - size[0] / 2
        y = h / 2 - size[1] / 2
        self.geometry("%dx%d+%d+%d" % (size + (x, y)))

    def search(self):
        # Clear previous results
        for widget in self.results_inner_frame.winfo_children():
            widget.destroy()

        options = webdriver.FirefoxOptions()
        options.add_argument('--headless')
        browser = webdriver.Firefox(options=options)

        channel_name_query = self.search_var.get()
        browser.get(f'https://www.youtube.com/results?search_query={channel_name_query}&sp=EgIQAg%253D%253D')
        browser.implicitly_wait(10)
        soup = BeautifulSoup(browser.page_source, 'html.parser')
        browser.quit()

        channel_elements = soup.find_all('a', {'class': 'channel-link'})
        for channel in channel_elements:
            channel_name = channel.text.strip().split("\n")[0]
            handle = channel['href'].split('/')[-1]
            display_name = f"{channel_name} ({handle})" if channel_name and handle.startswith('@') else ""
            if not display_name:
                continue

            thumbnail_img = channel.find_previous('yt-img-shadow').find("img", {"id": "img"})
            thumbnail_url = "https:" + thumbnail_img['src'] if thumbnail_img and thumbnail_img.has_attr('src') else None

            frame = tk.Frame(self.results_inner_frame)
            frame.pack(fill=tk.X, padx=10, pady=5)

            if thumbnail_url:
                img_data = requests.get(thumbnail_url).content
                img = Image.open(BytesIO(img_data))
                img = img.resize((50, 50), resample=Image.LANCZOS)
                img = ImageTk.PhotoImage(img)
                label = tk.Label(frame, image=img)
                label.image = img
                label.pack(side=tk.LEFT, padx=10)

            tk_label = tk.Label(frame, text=display_name, anchor="w")
            tk_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

            btn = tk.Button(frame, text="Subscribe", command=lambda name=display_name: self.subscribe_channel(name))
            btn.pack(side=tk.RIGHT)

        # Adjust canvas scroll region to encompass all widgets
        self.results_canvas.configure(scrollregion=self.results_canvas.bbox("all"))

    def subscribe_channel(self, channel_name_with_handle):
        if channel_name_with_handle and channel_name_with_handle not in self.subscribed_channels_listbox.get(0, tk.END):
            self.subscribed_channels_listbox.insert(tk.END, channel_name_with_handle)
            handle = channel_name_with_handle.split('(')[-1].replace(')', '').strip()
            current_video_urls = self.get_latest_video_urls(handle)

            videos_list = [current_video_urls[0]] if len(current_video_urls) > 0 else []
            shorts_list = [current_video_urls[1]] if len(current_video_urls) > 1 else []

            self.LAST_VIDEO_URLS[handle] = {
                "videos": videos_list,
                "shorts": shorts_list
            }
            notification.notify(
                title="YouTube Notifier",
                message=f"Subscribed to {channel_name_with_handle}",
                timeout=3
            )

    def delete_channel(self):
        selected = self.subscribed_channels_listbox.curselection()
        if selected:
            channel_name_with_handle = self.subscribed_channels_listbox.get(selected[0])
            self.subscribed_channels_listbox.delete(selected[0])

            handle = channel_name_with_handle.split('(')[-1].replace(')', '').strip()
            if handle in self.LAST_VIDEO_URLS:
                del self.LAST_VIDEO_URLS[handle]
            self.save_to_json()
        else:
            messagebox.showwarning("Warning", "Select a channel to delete!")


app = YouTubeNotifier()
app.mainloop()