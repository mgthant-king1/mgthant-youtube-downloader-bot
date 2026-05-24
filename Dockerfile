async def search_and_show_playlist(update: Update, message_obj, query_text, page=0):
    clean_query = query_text.replace('\n', ' ').strip()
    
    # 👈 အောက်ပါ ydl_opts ထဲတွင် 'cookiefile': 'cookies.txt' ထပ်ပေါင်းထည့်ပါ
    ydl_opts = {
        'playlistend': 20, 
        'quiet': True, 
        'extract_flat': 'in_playlist', 
        'geo_bypass': True, 
        'proxy': PROXY_URL,
        'cookiefile': 'cookies.txt' 
    }
