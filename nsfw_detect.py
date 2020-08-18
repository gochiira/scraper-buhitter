import requests
r = requests.post(
    "https://api.deepai.org/api/nsfw-detector",
    data={
        'image': 'https://pbs.twimg.com/media/EfkkjT2UwAAaxjI?format=jpg&name=900x900',
    },
    headers={'api-key': 'quickstart-QUdJIGlzIGNvbWluZy4uLi4K'}
)
print(r.json())
