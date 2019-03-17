import json

import requests

API_KEY = 'Riv5bNRAMEGJ4TR3s0GutEj7s'
BASE_URL = 'http://172.17.0.2'


class Formatter(object):
    @staticmethod
    def replace_contentcontainer_with_space(result):
        """
        Replaces contentcontainer_id with space_id to allow more usability from users
        """
        if 'results' in result:
            data = result['results']
        else:
            data = [result]

        for item in data:
            if 'content' in item and 'metadata' in item['content'] and 'contentcontainer_id' in item['content'][
                'metadata']:
                item['content']['metadata']['space_id'] = item['content']['metadata'].pop('contentcontainer_id')
        return result


class Request(object):
    def __init__(self, base_url, api_key):
        self.base_url = base_url
        self.api_key = api_key

    @property
    def headers(self):
        if not hasattr(self, '_headers'):
            self._headers = {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer {0}'.format(self.api_key)
            }

        return self._headers

    @property
    def session(self):
        if not hasattr(self, '_session'):
            self._session = requests.Session()
            self._session.headers.update(self.headers)
        return self._session

    def respond(self, response, formatter=None):
        if response.status_code == 404:
            return {'code': 404, 'message': '{} not found'.format(response.url), 'name': 'Not Found'}
        if response.status_code == 401:
            return {'code': 401, 'message': 'Check your API key', 'name': 'Not Authorized'}
        if response.status_code == 500:
            return {'code': 500, 'message': '', 'name': 'Internal Server Error'}

        result = response.json()
        if formatter:
            return formatter(result)
        return result

    def ensure_path(self, path):
        if not path.startswith('/'):
            path = '/{}'.format(path)
        return path

    def get(self, path, formatter=None, **kwargs):
        url = '{0}{1}'.format(self.base_url, self.ensure_path(path))

        if kwargs:
            url = '{}?'.format(url)
            for arg, value in kwargs.items():
                url = url + '{}={}&'.format(arg, value)
            url = url.strip('&')

        return self.respond(self.session.get(url), formatter)

    def post(self, path, payload, formatter=None):
        return self.respond(
            self.session.post('{0}{1}'.format(self.base_url, self.ensure_path(path)), json.dumps(payload)), formatter)

    def put(self, path, payload, formatter=None):
        return self.respond(
            self.session.put('{0}{1}'.format(self.base_url, self.ensure_path(path)), json.dumps(payload)), formatter)

    def patch(self, path, payload, formatter=None):
        return self.respond(
            self.session.patch('{0}{1}'.format(self.base_url, self.ensure_path(path)), json.dumps(payload)), formatter)

    def delete(self, path, formatter=None):
        return self.respond(self.session.delete('{0}{1}'.format(self.base_url, self.ensure_path(path))), formatter)


class Api(object):
    def __init__(self, request):
        self.request = request


class UserAPI(Api):
    def list(self, query=None):
        if not query:
            return self.request.get('/user')
        return self.request.get('/user', q=query)

    def create(self, username, email, password, firstname, lastname, title=None, gender=None, street=None, city=None, country=None, zip=None):

        data = {
            "account": {
                "username": username,
                "email": email
            },
            "profile": {
                "firstname": firstname,
                "lastname": lastname,
                "title": title,
                "gender": gender,
                "street": street,
                "city": city,
                "zip": zip,
                "country": Country.get_code(country)
            },
            "password": {
                "newPassword": password
            }
        }

        return self.request.post('/user', data)

    def get(self, user_id):
        return self.request.get('/user/{}'.format(user_id))

    def update(self, user_id, username=None, email=None, password=None, firstname=None, lastname=None, title=None, gender=None, street=None, city=None, country=None, zip=None, enabled=None):
        """
        IMPORTANT: Set Parameter value to '' if you want to remove it, otherwise it will be ignored
        """
        data = {}

        if username is not None or email is not None:
            data['account'] = {}
            if username is not None:
                data['account']['username'] = username
            if email is not None:
                data['account']['email'] = email

        if password is not None:
            data['password'] = {'newPassword': password}

        if firstname is not None or lastname is not None or title is not None or gender is not None or street is not None or city is not None or country is not None or zip is not None:
            data['profile'] = {}
            if firstname is not None:
                data['profile']['firstname'] = firstname
            if lastname is not None:
                data['profile']['lastname'] = lastname
            if title is not None:
                data['profile']['title'] = title
            if gender is not None:
                data['profile']['gender'] = gender
            if street is not None:
                data['profile']['street'] = street
            if city is not None:
                data['profile']['city'] = city
            if zip is not None:
                data['profile']['zip'] = zip
            if country is not None:
                data['profile']['country'] = Country.get_code(country)

            if enabled is not None:
                if enabled:
                    data['account']['enabled'] = 1
                else:
                    data['account']['enabled'] = 0

        return self.request.put('/user/{}'.format(user_id), data)

    def delete(self, user_id):
        return self.request.delete('/user/full/{}'.format(user_id))

    def log_out(self, user_id):
        return self.request.delete('/user/session/all/{}'.format(user_id))

    def enable(self, user_id):
        data = {'account': {'status': 1}}
        return self.request.put('/user/{}'.format(user_id), data)

    def disable(self, user_id):
        data = {'account': {'status': 0}}
        return self.request.put('/user/{}'.format(user_id), data)


class CommentApi(Api):
    def get(self, comment_id):
        return self.request.get('/comment/{}'.format(comment_id))


class PostAPI(Api):
    def list(self, space_id=None):
        if space_id:
            return self.request.get('/post/container/{}'.format(space_id),
                                    formatter=Formatter.replace_contentcontainer_with_space)
        return self.request.get('/post', formatter=Formatter.replace_contentcontainer_with_space)

    def get(self, post_id):
        return self.request.get('/post/{}'.format(post_id), formatter=Formatter.replace_contentcontainer_with_space)

    def delete(self, post_id):
        return self.request.delete('/post/{}'.format(post_id))

    def update(self, post_id, message):
        data = {
            "post": {
                "message": message
            }
        }

        return self.request.put('/post/{}'.format(post_id), data,
                                formatter=Formatter.replace_contentcontainer_with_space)

    def create(self, space_id, message):
        data = {
            "post": {
                "message": message
            }
        }
        return self.request.post('/post/container/{}'.format(space_id), data,
                                 formatter=Formatter.replace_contentcontainer_with_space)


class SpaceAPI(Api):

    def get(self, space_id):
        return self.request.get('/space/{}'.format(space_id))

    def list(self, query=None):
        if not query:
            return self.request.get('/space')
        return self.request.get('/space', q=query)

    def delete(self, space_id):
        return self.request.delete('/space/{}'.format(space_id))

    def create(self, name, description=None, private=False, tags=[], join_policy_invites_only=False):
        """
        :param join_policy_invites_only: only used when space is public, if false means invites & requests
        :return:
        """

        data = {
            "space": {
                "name": name,
                "description": description,
                "tags": ','.join(tags),
                "visibility": 0 if private else 1,  # 0 means members only, 1 means for registerd users
            }
        }

        if not private:
            data['space']['join_policy'] = 0 if join_policy_invites_only else 1
        else:
            data['space']['join_policy'] = 0
        return self.request.post('/space', data)

    def enable(self, space_id):
        data = {'space': {'status': 1}}
        return self.request.put('/space/{}'.format(space_id), data)

    def disable(self, space_id):
        data = {'space': {'status': 0}}
        return self.request.put('/space/{}'.format(space_id), data)

    def archive(self, space_id):
        data = {'space': {'status': 2}}
        return self.request.put('/space/{}'.format(space_id), data)

    def update(self, space_id, name=None, description=None, tags=None, private=None, join_policy_invites_only=None):
        data = {
            'space': {}
        }

        if name:
            data['space']['name'] = name
            data['space']['url'] = name

        if description:
            data['space']['description'] = description

        if tags is not None:
            data['space']['tags'] = ','.join(tags)

        if private is not None:
            if private is True:
                data['space']['visibility'] = 0
                data['space']['join_policy'] = 0
            else:
                data['space']['visibility'] = 1
                if join_policy_invites_only is not None:

                    data['space']['join_policy'] = 0 if join_policy_invites_only is True else 1

        return self.request.put('/space/{}'.format(space_id), data)


class LikeAPI(Api):
    def get(self, like_id):
        return self.request.get('/like/{}'.format(like_id))

    def unlike(self, like_id):
        return self.request.delete('/like/{}'.format(like_id))

    def list(self, post_id=None, comment_id=None, wiki_page_id=None):
        if post_id:
            return self.request.get('/like/type/post/{}'.format(post_id))
        if comment_id:
            return self.request.get('/like/type/comment/{}'.format(comment_id))
        if wiki_page_id:
            return self.request.get('/like/type/wikipage/{}'.format(wiki_page_id))
        return self.request.get('/like')

    def like(self, post_id=None, comment_id=None, wiki_page_id=None, ):
        if post_id:
            return self.request.put('/like/type/post/{}'.format(post_id), {})
        if comment_id:
            return self.request.put('/like/type/comment/{}'.format(comment_id), {})
        if wiki_page_id:
            return self.request.put('/like/type/wikipage/{}'.format(wiki_page_id), {})
        return {'code': 404, 'message': 'Select post or comment or wiki page to like', 'name': 'Not Found'}


class WikiAPI(Api):
    def get(self, wiki_page_id):
        return self.request.get('/wiki/{}'.format(wiki_page_id),
                                formatter=Formatter.replace_contentcontainer_with_space)

    def list(self, space_id=None):
        if not space_id:
            return self.request.get('/wiki')
        return self.request.get('/wiki/container/{}'.format(space_id))

    def delete(self, wiki_page_id):
        return self.request.delete('/wiki/{}'.format(wiki_page_id))

    def create(self, title, space_id=None, user_id=None, content=None, is_category=False, parent_category_page_id=None, is_home=False, only_admin_can_edit=False, is_public=False):
        if space_id:
            res = self.request.get('/space/{}'.format(space_id))
            if 'code' in res and res['code'] != 200:
                return res

            container_id = res['contentcontainer_id']
        elif user_id:
            res = self.request.get('/user/{}'.format(user_id))
            if 'code' in res and res['code'] != 200:
                return res

            container_id = res['account']['contentcontainer_id']

        data = {
                "title": title,
                "is_home": 1 if is_home else 0,
                "is_category": 1 if is_category else 0,
                "protected": 1 if only_admin_can_edit else 0,
                "parent_page_id": parent_category_page_id,
                "is_public": 1 if is_public else 0,
                "content": content
        }

        if is_category:
            data['wikipage'].pop('parent_category_page_id')

        return self.request.post('/wiki/container/{}'.format(container_id), data)

    def update(self, wiki_page_id, title, content=None, is_category=None, parent_category_page_id=None, is_home=None, only_admin_can_edit=None, is_public=None):
        data = {
                "title": title,
                "content": content
        }

        if is_category is not None:
            data['is_category'] = 1 if is_category else 0

        if parent_category_page_id is not None:
            data['parent_category_page_id'] = parent_category_page_id

        if is_category is not None:
            data['is_category'] = 1 if is_category else 0

        if is_home is not None:
            data['is_home'] = 1 if is_home else 0

        if only_admin_can_edit is not None:
            data['only_admin_can_edit'] = 1 if only_admin_can_edit else 0

        if is_public is not None:
            data['is_public'] = 1 if is_public else 0

        return self.request.put('/wiki/{}'.format(wiki_page_id), data)


    def migrate(self, from_use_id=None, from_space_id=None, to_user_id=None, to_space_id=None):
        from_container = None
        to_container = None

        if from_use_id:
            res = self.request.get('/user/{}'.format(from_use_id))
            if 'code' in res and res['code'] != 200:
                return res
            from_container = res['account']['contentcontainer_id']
        if to_user_id:
            res = self.request.get('/user/{}'.format(to_user_id))
            if 'code' in res and res['code'] != 200:
                return res
            to_container = res['account']['contentcontainer_id']

        if from_space_id:
            res = self.request.get('/space/{}'.format(from_space_id))
            if 'code' in res and res['code'] != 200:
                return res
            from_container = res['contentcontainer_id']

        if to_space_id:
            res = self.request.get('/space/{}'.format(to_space_id))
            if 'code' in res and res['code'] != 200:
                return res
            to_container = res['contentcontainer_id']
        return self.request.post('/wiki/migrate/{0}/{1}'.format(from_container, to_container))


class HumhubClient(object):
    def __init__(self, base_url, api_key):
        self.base_url = '{}/humhub/api/v1'.format(base_url)
        self.api_key = api_key

    @property
    def request(self):
        if not hasattr(self, '_request'):
            self._request = Request(self.base_url, self.api_key)
        return self._request

    @property
    def users(self):
        return UserAPI(self.request)

    @property
    def comments(self):
        return CommentApi(self.request)

    @property
    def users(self):
        return UserAPI(self.request)

    @property
    def spaces(self):
        return SpaceAPI(self.request)

    @property
    def contents(self):
        return ContentAPI(self.request)

    @property
    def files(self):
        return FileAPI(self.request)

    @property
    def likes(self):
        return LikeAPI(self.request)

    @property
    def posts(self):
        return PostAPI(self.request)

    @property
    def wikis(self):
        return WikiAPI(self.request)


class Country(object):
    COUNTRIES = {
        'Afghanistan': 'AF',
        'Aland Islands': 'AX',
        'Albania': 'AL',
        'Algeria': 'DZ',
        'American Samoa': 'AS',
        'Andorra': 'AD',
        'Angola': 'AO',
        'Anguilla': 'AI',
        'Antarctica': 'AQ',
        'Antigua &amp; Barbuda': 'AG',
        'Argentina': 'AR',
        'Armenia': 'AM',
        'Aruba': 'AW',
        'Australia': 'AU',
        'Austria': 'AT',
        'Azerbaijan': 'AZ',
        'Bahamas': 'BS',
        'Bahrain': 'BH',
        'Bangladesh': 'BD',
        'Barbados': 'BB',
        'Belarus': 'BY',
        'Belgium': 'BE',
        'Belize': 'BZ',
        'Benin': 'BJ',
        'Bermuda': 'BM',
        'Bhutan': 'BT',
        'Bolivia': 'BO',
        'Bosnia &amp; Herzegovina': 'BA',
        'Botswana': 'BW',
        'Bouvet Island': 'BV',
        'Brazil': 'BR',
        'British Indian Ocean Territory': 'IO',
        'British Virgin Islands': 'VG',
        'Brunei': 'BN',
        'Bulgaria': 'BG',
        'Burkina Faso': 'BF',
        'Burundi': 'BI',
        'Cambodia': 'KH',
        'Cameroon': 'CM',
        'Canada': 'CA',
        'Cape Verde': 'CV',
        'Caribbean Netherlands': 'BQ',
        'Cayman Islands': 'KY',
        'Central African Republic': 'CF',
        'Chad': 'TD',
        'Chile': 'CL',
        'China': 'CN',
        'Christmas Island': 'CX',
        'Cocos (Keeling) Islands': 'CC',
        'Colombia': 'CO',
        'Comoros': 'KM',
        'Congo ': 'CD',
        'Cook Islands': 'CK',
        'Costa Rica': 'CR',
        'Côte d’Ivoire': 'CI',
        'Croatia': 'HR',
        'Cuba': 'CU',
        'Curaçao': 'AN',
        'Cyprus': 'CY',
        'Czechia': 'CZ',
        'Denmark': 'DK',
        'Djibouti': 'DJ',
        'Dominica': 'DM',
        'Dominican Republic': 'DO',
        'Ecuador': 'EC',
        'Egypt': 'EG',
        'Equatorial Guinea': 'GQ',
        'Eritrea': 'ER',
        'Estonia': 'EE',
        'Ethiopia': 'ET',
        'Falkland Islands': 'FK',
        'Faroe Islands': 'FO',
        'Fiji': 'FJ',
        'Finland': 'FI',
        'France': 'FR',
        'French Guiana': 'GF',
        'French Polynesia': 'PF',
        'French Southern Territories': 'TF',
        'Gabon': 'GA',
        'Gambia': 'GM',
        'Georgia': 'GE',
        'Germany': 'DE',
        'Ghana': 'GH',
        'Gibraltar': 'GI',
        'Greece': 'GR',
        'Greenland': 'GL',
        'Grenada': 'GD',
        'Guadeloupe': 'GP',
        'Guam': 'GU',
        'Guatemala': 'GT',
        'Guernsey': 'GG',
        'Guinea': 'GW',
        'Guyana': 'GY',
        'Haiti': 'HT',
        'Heard &amp; McDonald Islands': 'HM',
        'Honduras': 'HN',
        'Hong Kong SAR China': 'HK',
        'Hungary': 'HU',
        'Iceland': 'IS',
        'India': 'IN',
        'Indonesia': 'ID',
        'Iran': 'IR',
        'Iraq': 'IQ',
        'Ireland': 'IE',
        'Isle of Man': 'IM',
        'Israel': 'IL',
        'Italy': 'IT',
        'Jamaica': 'JM',
        'Japan': 'JP',
        'Jersey': 'JE',
        'Jordan': 'JO',
        'Kazakhstan': 'KZ',
        'Kenya': 'KE',
        'Kiribati': 'KI',
        'Kosovo': 'XK',
        'Kuwait': 'KW',
        'Kyrgyzstan': 'KG',
        'Laos': 'LA',
        'Latvia': 'LV',
        'Lebanon': 'LB',
        'Lesotho': 'LS',
        'Liberia': 'LR',
        'Libya': 'LY',
        'Liechtenstein': 'LI',
        'Lithuania': 'LT',
        'Luxembourg': 'LU',
        'Macau SAR China': 'MO',
        'Macedonia': 'MK',
        'Madagascar': 'MG',
        'Malawi': 'MW',
        'Malaysia': 'MY',
        'Maldives': 'MV',
        'Mali': 'ML',
        'Malta': 'MT',
        'Marshall Islands': 'MH',
        'Martinique': 'MQ',
        'Mauritania': 'MR',
        'Mauritius': 'MU',
        'Mayotte': 'YT',
        'Mexico': 'MX',
        'Micronesia': 'FM',
        'Moldova': 'MD',
        'Monaco': 'MC',
        'Mongolia': 'MN',
        'Montenegro': 'ME',
        'Montserrat': 'MS',
        'Morocco': 'MA',
        'Mozambique': 'MZ',
        'Myanmar (Burma)': 'MM',
        'Namibia': 'NA',
        'Nauru': 'NR',
        'Nepal': 'NP',
        'Netherlands': 'NL',
        'New Caledonia': 'NC',
        'New Zealand': 'NZ',
        'Nicaragua': 'NI',
        'Niger': 'NE',
        'Nigeria': 'NG',
        'Niue': 'NU',
        'Norfolk Island': 'NF',
        'North Korea': 'KP',
        'Northern Mariana Islands': 'MP',
        'Norway': 'NO',
        'Oman': 'OM',
        'Pakistan': 'PK',
        'Palau': 'PW',
        'Palestinian Territories': 'PS',
        'Panama': 'PA',
        'Papua New Guinea': 'PG',
        'Paraguay': 'PY',
        'Peru': 'PE',
        'Philippines': 'PH',
        'Pitcairn Islands': 'PN',
        'Poland': 'PL',
        'Portugal': 'PT',
        'Puerto Rico': 'PR',
        'Qatar': 'QA',
        'Réunion': 'RE',
        'Romania': 'RO',
        'Russia': 'RU',
        'Rwanda': 'RW',
        'Samoa': 'WS',
        'San Marino': 'SM',
        'São Tomé &amp; Príncipe': 'ST',
        'Saudi Arabia': 'SA',
        'Senegal': 'SN',
        'Serbia': 'RS',
        'Seychelles': 'SC',
        'Sierra Leone': 'SL',
        'Singapore': 'SG',
        'Sint Maarten': 'SX',
        'Slovakia': 'SK',
        'Slovenia': 'SI',
        'Solomon Islands': 'SB',
        'Somalia': 'SO',
        'South Africa': 'ZA',
        'South Georgia &amp; South Sandwich Islands': 'GS',
        'South Korea': 'KR',
        'South Sudan': 'SS',
        'Spain': 'ES',
        'Sri Lanka': 'LK',
        'St. Barthélemy': 'BL',
        'St. Helena': 'SH',
        'St. Kitts &amp; Nevis': 'KN',
        'St. Lucia': 'LC',
        'St. Martin': 'MF',
        'St. Pierre &amp; Miquelon': 'PM',
        'St. Vincent &amp; Grenadines': 'VC',
        'Sudan': 'SD',
        'Suriname': 'SR',
        'Svalbard &amp; Jan Mayen': 'SJ',
        'Swaziland': 'SZ',
        'Sweden': 'SE',
        'Switzerland': 'CH',
        'Syria': 'SY',
        'Taiwan': 'TW',
        'Tajikistan': 'TJ',
        'Tanzania': 'TZ',
        'Thailand': 'TH',
        'Timor': 'TL',
        'Togo': 'TG',
        'Tokelau': 'TK',
        'Tonga': 'TO',
        'Trinidad &amp; Tobago': 'TT',
        'Tunisia': 'TN',
        'Turkey': 'TR',
        'Turkmenistan': 'TM',
        'Turks &amp; Caicos Islands': 'TC',
        'Tuvalu': 'TV',
        'U.S. Outlying Islands': 'UM',
        'U.S. Virgin Islands': 'VI',
        'Uganda': 'UG',
        'Ukraine': 'UA',
        'United Arab Emirates': 'AE',
        'United Kingdom': 'GB',
        'United States': 'US',
        'Uruguay': 'UY',
        'Uzbekistan': 'UZ',
        'Vanuatu': 'VU',
        'Vatican City': 'VA',
        'Venezuela': 'VE',
        'Vietnam': 'VN',
        'Wallis &amp; Futuna': 'WF',
        'Western Sahara': 'EH',
        'Yemen': 'YE',
        'Zambia': 'ZM',
        'Zimbabwe': 'ZW'
    }

    @staticmethod
    def get_code(country):
        return Country.COUNTRIES[country]
