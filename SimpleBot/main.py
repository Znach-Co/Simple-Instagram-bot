from instagram_private_api import Client, errors
from instagram_private_api.compat import compat_http_client
import json
import pickle
import os
import random
import time
import traceback
from datetime import datetime, timedelta
from copy import deepcopy

random.seed(datetime.now())

BOT_FOLDER = os.path.dirname(__file__)
BOT_CONFIGS = os.path.join(BOT_FOLDER, 'config.json')


def get_configs(path):
    """
    Read config file

    :param path:
    :return:
    """
    with open(path) as f:
        data = json.load(f)
    return data


def if_exists(folder):
    """
    Create folder for cookies

    :param folder:
    :return:
    """
    if os.path.exists(os.path.join(BOT_FOLDER, folder)):
        return os.path.join(BOT_FOLDER, folder)
    else:
        os.mkdir(os.path.join(BOT_FOLDER, folder))
        return os.path.join(BOT_FOLDER, folder)


class ClientPickle(Client):
    """Class for storing user's cookies from API"""

    def __init__(self, *args, **kwargs):
        """
        Initialization of Client class with pickle functionality

        :param args:
        :param kwargs:
        """
        _cookies_path = if_exists("cookies")
        pcl_files = os.listdir(_cookies_path)
        if args:
            user = args[0]
        else:
            user = kwargs['user']

        checker = [1 for i in pcl_files if i.split('.')[0] == user]

        if checker:
            _cookies_path = os.path.join(_cookies_path, f'{user}.pickle')
            with open(_cookies_path, 'rb') as f:
                _cookies = pickle.load(f)

            new_kwargs = {**kwargs, **_cookies}
            super(ClientPickle, self).__init__(*args, **new_kwargs)
            self.login()
        else:
            super(ClientPickle, self).__init__(*args, **kwargs)

    def before_exit(self):
        """
        Save cookies to pickle before exit

        :return:
        """
        user = self.username
        _cookies_path = if_exists("cookies")
        _cookies_path = os.path.join(_cookies_path, f'{user}.pickle')

        with open(_cookies_path, 'wb') as f:
            pickle.dump(self.settings, f)


class SIBot:
    """Main class for all actions and processes"""

    last_ts = 0.0
    monitored_users = []
    media_to_like = 0
    users_to_follow = 0

    self_followings = []
    self_followers = []

    def __init__(self):
        """Reading configs"""
        self.__configs = get_configs(BOT_CONFIGS)

        """credentials"""
        __creds = self.__configs.pop('credentials', {})
        if __creds:
            self.user = __creds.get('user', '')
            __password = __creds.get('password', '')
            if not self.user or not __password:
                raise Exception('Please, provide your credentials(username and password) in config.json')
        else:
            raise Exception('Please, provide your credentials(username and password) in config.json')

        self.api = ClientPickle(self.user, __password)

        """other settings"""
        self.limits_per_hour = self.__configs.pop('limitsPerHour', {})
        self.search_hashtags = self.__configs.pop('hashtags', [])
        self.process = self.__configs.pop('process', None)
        self.duration = self.__configs.pop('duration', {})
        self.white_list = self.__configs.pop('whiteList', [])

        if not self.limits_per_hour or not self.search_hashtags or \
            not self.process or not self.duration:
            raise Exception('Please, provide all necessary parameters(limitsPerHour, hashtags, process, duration)'
                            ' in config.json')

        self.check_parameters()
        self.search_hashtags = [i.replace('#', '') for i in self.search_hashtags]
        self.white_list = [i.replace('@', '') for i in self.white_list]

        """Reading followers and pickle with monitoring data"""

        if self.process:
            _monitored_data_path = if_exists("additional_data")
            _monitored_current_data = os.path.join(_monitored_data_path, f"{self.user}_monitoring.pickle")

            if os.path.exists(_monitored_current_data):
                with open(_monitored_current_data, 'rb') as f:
                    data = pickle.load(f)
                    self.monitored_users = data['monitored_users']
                    self.last_ts = float(data['last_ts'])

    def dump_all(self):
        """
        Finish bot process, dump settings and users
        :return:
        """
        _monitored_data_path = if_exists("additional_data")
        _monitored_current_data = os.path.join(_monitored_data_path, f"{self.user}_monitoring.pickle")
        data = {'monitored_users': self.monitored_users, 'last_ts': datetime.now().timestamp()}
        with open(_monitored_current_data, 'wb') as f:
            pickle.dump(data, f)

        self.api.before_exit()

    def liking(self, media_id):
        """
        Like media

        :param media_id:
        :return:
        """
        try:
            _ = self.api.post_like(media_id)
        except Exception as e:
            print(e)

    def following(self, user_id):
        """
        Follow user

        :param user_id:
        :return:
        """
        try:
            creat = self.api.friendships_create(user_id)
            return creat.get('friendship_status', '').get('following')
        except Exception as e:
            print(e)
            return False

    def following_and_storing(self, user_obj):
        """
        Follow user and store in file

        :param user_obj:
        :return:
        """
        if self.following(user_obj['user']):
            self.monitored_users.append({'user': user_obj['user'], 'username': user_obj['username'],
                                         'followDate': datetime.now().timestamp()})

    def unfollowing(self, user_id):
        """
        Unfollow user

        :param user_id:
        :return:
        """
        try:
            destroy = self.api.friendships_destroy(user_id)
            return not destroy.get('friendship_status', '').get('following')
        except errors.ClientError as e:
            return False

    def unfollowing_and_removing(self, user_id):
        """
        Unfollow user and remove from file

        :param user_id:
        :return:
        """
        if self.unfollowing(user_id):
            ind = [i for i, j in enumerate(self.monitored_users) if j.get('user', '') == user_id]
            if ind:
                self.monitored_users.remove(self.monitored_users[ind[0]])

    def get_followers(self):
        """
        Get self followers

        :return:
        """
        time.sleep(random.randint(10, 20))
        followers = self.api.user_followers(self.api.authenticated_user_id, rank_token=Client.generate_uuid())
        return followers

    def get_followings(self):
        """
        Get self followings

        :return:
        """
        time.sleep(random.randint(10, 20))
        followings = self.api.user_following(self.api.authenticated_user_id, rank_token=Client.generate_uuid())
        return followings

    def get_new_followers(self):
        """
        Get new followers from news_inbox
        :return:
        """
        time.sleep(random.randint(10, 20))
        news = self.api.news_inbox()
        if news.get('counts', {}).get('relationships') > 0:
            stories = news.get('new_stories', []) + news.get('old_stories', [])
            stories = list(filter(lambda x: x['story_type']==101 and x['args']['timestamp'] > self.last_ts, stories))
            new_followers = []
            for s in stories:
                args = s.get('args', {})
                if args.get('profile_id') and args.get('profile_id') not in new_followers:
                    new_followers.append(args.get('profile_id'))
                if args.get('second_profile_id') and args.get('second_profile_id') not in new_followers:
                    new_followers.append(args.get('second_profile_id'))
            return new_followers
        else:
            return []

    def check_if_suit(self, media):
        """
        Check if user suit for following (not friend or business)
        :param media:
        :return:
        """

        user_id = media.get('user', {}).get('pk', None)
        media_fr_st = media.get('user', {}).get('friendship_status', {})
        if media_fr_st:
            if media_fr_st.get('following', None):
                return False
            if media_fr_st.get('outgoing_request', None):
                return False

        if user_id:
            m_users = [u['user'] for u in self.monitored_users]
            if user_id in m_users:
                return False

            time.sleep(random.randint(5, 15))
            user_info = self.api.user_info(user_id)
            if user_info.get('user', {}).get('is_business', None) \
                    or user_info.get('user', {}).get('is_potential_business', None):
                return False

            time.sleep(random.randint(10, 15))
            friendship = self.api.friendships_show(user_id)
            if friendship.get('blocking', None):
                return False
            if friendship.get('followed_by', None):
                return False
        return True

    def get_user_media(self, user_id):
        """
        Get user's feed
        :param user_id:
        :return:
        """
        feed = self.api.user_feed(user_id)
        return feed

    def hashtag_feed_list(self, hashtags):
        """
        Get hashtags feed
        :param hashtags:
        :return:
        """
        next_max_ids = [1 for _ in range(len(hashtags))]
        gen_tokens = [Client.generate_uuid() for _ in range(len(hashtags))]

        while [1 for i in next_max_ids if i]:
            items = []
            for hashtag in hashtags:
                next_max_id = next_max_ids[hashtags.index(hashtag)]
                if next_max_id:
                    gen_token = gen_tokens[hashtags.index(hashtag)]

                    hashtag_items, next_max_id = self.hashtag_feed(hashtag, gen_token, next_max_id)

                    items.extend(hashtag_items)
                    next_max_ids[hashtags.index(hashtag)] = next_max_id
                else:
                    continue
            yield items

    def hashtag_feed(self, hashtag, gen_token, next_max_id):
        """
        Get hashtag feed
        :param hashtag:
        :param gen_token:
        :param next_max_id:
        :return:
        """
        time.sleep(random.randint(5, 15))
        tries = 0

        if next_max_id == 1:

            while tries < 5:
                try:
                    results = self.api.feed_tag(hashtag, gen_token)

                    return results.get('ranked_items', []) + results.get('items', []), results['next_max_id']
                except compat_http_client.IncompleteRead:
                    tries += 1
                    continue
            else:
                return [], next_max_id
        else:
            while tries < 5:
                try:
                    results = self.api.feed_tag(hashtag, gen_token, max_id=next_max_id)
                    return results.get('items', []), results['next_max_id']
                except compat_http_client.IncompleteRead:
                    tries += 1
                    continue
            else:
                return [], next_max_id

    @staticmethod
    def get_user_from_post(media_obj):
        """
        Get user_id and name from post
        :param media_obj:
        :return:
        """
        if media_obj:
            user_id = media_obj.get('user', {}).get('pk')
            user_name = media_obj.get('user', {}).get('username')
            return user_id, user_name
        return

    @staticmethod
    def get_media_id_from_post(media_obj):
        """
        Get media_id from post
        :param media_obj:
        :return:
        """
        if media_obj:
            media_id = media_obj.get('id')
            return media_id
        return

    def run(self):
        """
        Run the main process
        :return:
        """
        print('A simple bot started the process.')
        try:
            self.calculate_before_process()

            if self.process == "Like":
                self.process_like()
            elif self.process == "Like-and-follow":
                self.process_like_and_follow()
        except Exception:
            print(traceback.format_exc())
        finally:
            self.dump_all()
        print('A simple bot finished the process.')

    def process_like(self):
        """
        The process of liking
        :return:
        """
        medias = self.prepare_process_like()
        wait_time = 3600//(self.limits_per_hour.get('like') + 1)
        for m in medias:
            time.sleep(wait_time + trunc_gauss(0, 5, -30, 30))
            self.liking(m)

    def prepare_process_like(self):
        """
        Prepare media for liking process
        :return:
        """
        media = []

        feed_likes = self.media_to_like//2
        following_likes = round((self.media_to_like//2)*3/4)
        followers_likes = self.media_to_like - feed_likes - following_likes

        ids = []
        for posts in self.hashtag_feed_list(self.search_hashtags):
            if len(posts) > feed_likes:
                ids.extend([i['id'] for i in (random.choice(posts) for _ in range(feed_likes)) if i['id'] not in ids])
                break
            else:
                ids.extend([i['id'] for i in posts[:feed_likes] if i['id'] not in ids])
                feed_likes -= len(ids)
                if feed_likes < 0:
                    break

        media.extend(ids)
        followings = []
        media.extend([i for i in self.get_following_likes(followings, following_likes) if i and i not in media])

        media.extend([i for i in self.get_followers_likes(followers_likes) if i and i not in media])

        return media

    def get_following_likes(self, followings_list, following_likes):
        """

        :param followings_list:
        :param following_likes:
        :return:
        """
        user_followings = []
        if self.monitored_users:
            followings_list.extend([u['user'] for u in self.monitored_users])

        if len(followings_list) < following_likes:
            user_followings = self.get_followings()
            self.self_followings = deepcopy(user_followings)
            user_followings = [i['pk'] for i in user_followings.get('users', []) if i['pk'] not in followings_list]

            if user_followings:
                if len(user_followings) > following_likes - len(followings_list):
                    followings_list.extend(
                        [random.choice(user_followings) for _ in range(following_likes - len(followings_list))])
                else:
                    followings_list.extend(user_followings)
        else:
            followings_list = [random.choice(followings_list) for _ in range(following_likes)]

        followings_media_ids = [self.random_user_media(i) for i in followings_list]

        if len(followings_media_ids) < following_likes and user_followings:
            while len(followings_media_ids) < following_likes:
                u = random.choice(user_followings)
                rm = self.random_user_media(u)
                if rm and rm not in followings_media_ids:
                    followings_media_ids.append(rm)

        return followings_media_ids

    def get_to_unfollow(self, to_unfollow, n_unfollow):
        """
        Prepare list of users to unfollow
        :param to_unfollow:
        :param n_unfollow:
        :return:
        """
        if self.monitored_users:
            current_monitored = \
                list(filter(lambda x: datetime.fromtimestamp(float(x['followDate'])) + timedelta(days=14)
                                      < datetime.now() and x['username'] not in self.white_list, self.monitored_users))
            to_unfollow.extend([u['user'] for u in current_monitored])

        if len(to_unfollow) < n_unfollow:
            if not self.self_followings:
                self.self_followings = self.get_followings()
            add_followings = [f['pk'] for f in self.self_followings.get('users', [])
                              if f['username'] not in self.white_list]

            if add_followings:
                if len(add_followings) > n_unfollow - len(to_unfollow):
                    to_unfollow.extend([random.choice(add_followings) for _ in range(n_unfollow - len(to_unfollow))])
                else:
                    to_unfollow.extend(add_followings)
        else:
            to_unfollow = [random.choice(to_unfollow) for _ in range(n_unfollow)]

        return to_unfollow

    def get_followers_likes(self, followers_likes):
        """
        Prepare followers media to like
        :param followers_likes:
        :return:
        """
        user_followers = []

        followers = self.get_new_followers()
        if len(followers) < followers_likes:
            user_followers = self.get_followers()
            self.self_followers = deepcopy(user_followers)
            user_followers = [i['pk'] for i in user_followers.get('users', []) if i['pk'] not in followers]

            if user_followers:
                if len(user_followers) > followers_likes - len(followers):
                    followers.extend([random.choice(user_followers) for _ in range(followers_likes - len(followers))])
                else:
                    followers.extend(user_followers)
        else:
            followers = [random.choice(followers) for _ in range(followers_likes)]

        followers_media_ids = [self.random_user_media(i) for i in followers]

        if len(followers_media_ids) < followers_likes and user_followers:
            while len(followers_media_ids) < followers_likes:
                u = random.choice(user_followers)
                rm = self.random_user_media(u)
                if rm and rm not in followers_media_ids:
                    followers_media_ids.append(rm)

        return followers_media_ids

    def random_user_media(self, user_id):
        """
        Get random media from user's feed
        :param user_id:
        :return:
        """
        try:
            time.sleep(random.randint(10, 15))
            feed = self.get_user_media(user_id)
            items = [i for i in feed.get('items', []) if not i.get('has_liked', False)]
            items = sorted(items[:6], key=lambda x: x['like_count'], reverse=True)
            if items:
                return items[0].get('id')
            else:
                return None
        except Exception:
            return None

    def process_like_and_follow(self):
        """
        The process of liking, following and unfollowing
        :return:
        """
        follow, media, unfollow = self.prepare_process_like_and_follow()
        follow_acts, media_acts, unfollow_acts = len(follow), len(media), len(unfollow)
        all_acts = round(self.limits_per_hour.get('follow') + self.limits_per_hour.get('like') +
                         self.limits_per_hour.get('unfollow'))
        wait_time = 3600 // all_acts + 1
        while follow_acts or media_acts or unfollow_acts:
            time.sleep(wait_time + trunc_gauss(0, 5, -30, 30))
            rc = random.choices(['f', 'l', 'u'], [follow_acts, media_acts, unfollow_acts])[0]

            if rc == 'f':
                fo = follow.pop(0)
                self.following_and_storing(fo)
                follow_acts -= 1
            elif rc == 'l':
                mo = media.pop(0)
                self.liking(mo)
                media_acts -= 1
            elif rc == 'u':
                uo = unfollow.pop(0)
                self.unfollowing_and_removing(uo)
                unfollow_acts -= 1

    def prepare_process_like_and_follow(self):
        """
        Prepare data for liking and following process
        :return:
        """
        follow = []
        media = []
        unfollow = []

        coef = self.users_to_follow / self.limits_per_hour.get('follow', 1)
        media_to_like = round(coef*self.limits_per_hour.get('like'))
        num_to_unfollow = round(coef*self.limits_per_hour.get('unfollow'))

        feed_likes = media_to_like // 2
        feed_likes_list = []
        following_likes = round((media_to_like // 2) * 3 / 4)
        following_likes_list = []
        followers_likes = media_to_like - feed_likes - following_likes

        monitored_ids = [i["user"] for i in self.monitored_users]

        for posts in self.hashtag_feed_list(self.search_hashtags):
            if len(follow) < self.users_to_follow:
                for m in posts:
                    if self.check_if_suit(m):
                        user_id, username = self.get_user_from_post(m)
                        if user_id and user_id not in [i["user"] for i in follow] \
                                and user_id not in monitored_ids:
                            follow.append({'user': user_id, 'username': username})
                            following_likes_list.append(m)

                    if len(follow) >= self.users_to_follow:
                        break

                for p in following_likes_list:
                    if p in posts:
                        posts.remove(p)

            if feed_likes > 0:
                if len(posts) > feed_likes:
                    feed_likes_list.extend([i['id'] for i in (random.choice(posts) for _ in range(feed_likes))
                                            if i['id'] not in feed_likes_list])
                else:
                    feed_likes_list.extend([i['id'] for i in posts[:feed_likes] if i['id'] not in feed_likes_list])
                feed_likes -= len(feed_likes_list)
                if feed_likes <= 0:
                    if len(follow) >= self.users_to_follow:
                        break
            if len(follow) >= self.users_to_follow and feed_likes <= 0:
                break

        media.extend(feed_likes_list)

        if len(following_likes_list) < following_likes:
            followings = []
            get_n_followings = following_likes - len(following_likes_list)
            if following_likes_list:
                following_likes_list = [self.get_media_id_from_post(i) for i in following_likes_list]
            following_likes_list.extend([i for i in self.get_following_likes(followings, get_n_followings)
                                         if i and i not in media])
            media.extend(following_likes_list)
        else:
            media.extend([self.get_media_id_from_post(i) for i in following_likes_list[:following_likes]])

        media.extend([i for i in self.get_followers_likes(followers_likes) if i and i not in media])

        unfollow = self.get_to_unfollow(unfollow, num_to_unfollow)

        return follow, media, unfollow

    def calculate_before_process(self):
        """
        Prepare main value for process
        :return:
        """
        typ = self.duration.get('type')
        val = self.duration.get('value')

        if self.process == "Like":
            if typ == "by_time":
                self.media_to_like = round(val*self.limits_per_hour.get('like'))
            elif typ == "by_likes":
                self.media_to_like = round(val)

        elif self.process == "Like-and-follow":
            if typ == "by_time":
                self.users_to_follow = round(val*self.limits_per_hour.get('follow'))
            elif typ == "by_users":
                self.users_to_follow = round(val)

    def check_parameters(self):
        """
        Check parameters from configs
        :return:
        """

        if self.process not in ["Like", "Like-and-follow"]:
            raiser('process')

        if "type" not in self.duration or "value" not in self.duration:
            raiser('duration(type or value)')
        else:
            typ = self.duration['type']
            val = self.duration['value']
            if self.process == "Like":
                if typ not in ['by_time', 'by_likes']:
                    raiser('type')

                if "like" not in self.limits_per_hour:
                    raiser('limitsPerHour(like)')
                else:
                    try:
                        self.limits_per_hour['like'] = float(self.limits_per_hour['like'])
                    except ValueError:
                        raiser('like')
            elif self.process == "Like-and-follow":
                if typ not in ['by_time', 'by_users']:
                    raiser('type')

                if "like" not in self.limits_per_hour or "follow" not in self.limits_per_hour \
                        or "unfollow" not in self.limits_per_hour:
                    raiser('limitsPerHour(like or follow or unfollow)')
                else:
                    for i in ["like", "follow", "unfollow"]:
                        try:
                            self.limits_per_hour[i] = float(self.limits_per_hour[i])
                        except ValueError:
                            raiser(i)
            try:
                self.duration['value'] = float(val)
            except ValueError:
                raiser('value')

        if not isinstance(self.search_hashtags, list):
            raiser('hashtags')

        if not isinstance(self.white_list, list):
            raiser('whiteList')


def raiser(string):
    """
    Raise error if parameter missed
    :param string:
    :return:
    """
    raise Exception(f'Please check your config.json file, {string} is missed or wrong.')


def trunc_gauss(mu, sigma, bottom, top):
    """
    Generate number from normal distribution

    :param mu: mean
    :param sigma: step
    :param bottom: min
    :param top: max
    :return: int number
    """
    a = random.gauss(mu, sigma)
    while (bottom <= a <= top) is False:
        a = random.gauss(mu, sigma)
    return int(a)


if __name__ == "__main__":
    SI = SIBot()
    SI.run()
