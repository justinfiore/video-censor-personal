import json

try:
    with open('/Users/justinfiore/workspace/personal/video-censor-personal/output-video/The Family Plan-segments2.json', 'r') as f:
        data = json.load(f)
    for segment in data:
        if 'labels' in segment:
            segment['labels'] = [l for l in segment['labels'] if l == 'Profanity']
    with open('/Users/justinfiore/workspace/personal/video-censor-personal/output-video/The Family Plan-segments2.json', 'w') as f:
        json.dump(data, f, indent=2)
    print('Success')
except Exception as e:
    print(f'Error: {e}')
