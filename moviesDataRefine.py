from pymongo import MongoClient

if __name__ == "__main__":
    client = MongoClient('mongodb://localhost:27017/')
    db = client['91mjw']
    result = db.movies.find({})
    for record in result:
        _id = record['_id']
        old_episode = record['episode']
        new_episode = []
        for item in old_episode:
            megnet_link = item['megnet_link']
            if megnet_link != 'None':
                item['megnet_link'] = megnet_link.replace('\r','')
            new_episode.append(item)
        db.movies.find_one_and_update({'_id':_id}, {'$set': {'episode':new_episode}})