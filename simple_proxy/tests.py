import re

from bs4 import BeautifulSoup
from django.test import TestCase
from django.test.client import Client

from .views import ProxyView


class TestProxyClient(TestCase):
    def setUp(self):
        self.client = Client()
        self.test_html = '''
            <h2>
                <a href="https://habrahabr.ru/company/jugru/blog/327492/">№1 на Stack Overflow</a>
                <b>
                     О развитии .NET как платформы
                </b>
            </h2>
           '''

    def test_simple_get_page(self):

        response = self.client.get(path='/company/cloud4y/blog/327352/')
        self.assertEquals(response.status_code, 200)
        bs_content = BeautifulSoup(response.content, 'html.parser')
        title = bs_content.find(attrs={"class": "post__title-text"})  # post title
        self.assertEquals(
            ''.join(title.contents).strip(),
            'Анализ™ публикаций™ на Хабрахабре™ за последние™ полгода™. Статистика™, полезные™ находки™ и рейтинги™'
        )
        self.assertEquals(response.status_code, 200)

    def test_search_page(self):
        response = self.client.get(path='/search/?q=yandex#h')
        self.assertEquals(response.status_code, 200)

    def test_rewrite(self):
        test_proxy = ProxyView()
        test_proxy.base_url = 'https://habrahabr.ru/'
        test_proxy.host = '127.0.0.1:8000'
        new_content = test_proxy.rewrite_content(self.test_html)
        new_content = re.sub('[\s+]', '', new_content)
        test_content = '''
        <h2>
         <a href="http://127.0.0.1:8000/company/jugru/blog/327492/">№1 на Stack Overflow™</a>
          <b>
           О развитии™ .NET как платформы™
          </b>
        </h2>
        '''
        test_content = re.sub('[\s+]', '', test_content)
        self.assertEquals(new_content, test_content)
