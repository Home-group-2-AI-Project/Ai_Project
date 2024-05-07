def get_channels(app):
    try:
        result = app.client.conversations_list(types="public_channel")
        if result['ok']:
            all_channels = result['channels']
            channel_info_list = []
            for channel in all_channels:
                channel_info = {
                    'name_normalized': channel['name_normalized'],
                    'id': channel['id'],
                }
                channel_info_list.append(channel_info)
            return channel_info_list
        else:
            print(f"Error getting channels: {result['error']}")
            return []  # Return empty list on error
    except Exception as e:
        print(f"Error: {e}")
