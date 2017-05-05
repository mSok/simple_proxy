"""
View for proxy site
"""
import re
import html

import requests
import bs4

from django.http import HttpResponse
from django.views.generic import View

# excluded tags
EXCLUDED_TAGS = ['script', 'style', 'meta', 'html']
# pattern what we need replace in content
PATTERN_TO_REPLACE = re.compile(r'(?P<word>\b\w{6}\b)')
# for what we replace
PATTERN_REPLACED = r'\g<word>™'


class ProxyView(View):
    """
    Class for proxy site
    """
    base_url = ''
    url = ''
    params = {}
    method = ''

    def dispatch(self, request, url, *args, **kwargs):
        """
        Dispatch the http method to base site with params and rewrite if needed
        """
        self.url = url
        self.method = request.method
        self.params = request.GET
        self.host = request.get_host()
        response = super().dispatch(request, *args, **kwargs)
        if 'fonts' not in request.path:
            response.content = self.rewrite_content(response.content)
        return response

    def get_proxy_root(self):
        """
        Get proxy url for replace in static html content
        """
        return ''.join(['http://', self.host, '/'])

    def _filter_strings(self, item):
        """Filter bs4 elements to rewrite
        Args:
            item (bs.NavigableString): html page item

        Returns:
            (bool): needed to rewrite content
        """
        if any([
            isinstance(item, bs4.Comment),
            not isinstance(item, bs4.NavigableString),
            not item.string,
            not item.name not in EXCLUDED_TAGS,
            len(item.string or '') < 6
        ]):
            return False
        return True

    def _rewrite_string(self, node):
        """Method to rewrite html string content

        Args:
            node (bs.Tag):html element to rewrite

        Returns:
            None
        """
        for string_item in filter(self._filter_strings, node):
            string_item.string.replace_with(
                html.unescape(re.sub(PATTERN_TO_REPLACE, PATTERN_REPLACED, string_item.string))
            )

    def rewrite_content(self, content):
        """
        Method to rewrite response from base site
        """
        soup = bs4.BeautifulSoup(content, 'html.parser')
        # for tag in soup.find_all(href=re.compile(self.base_url)):
        #     tag['href'] = tag['href'].replace(self.base_url, self.get_proxy_root())
        for node in soup.find_all(True):
            if node.get('href', None) and re.search(self.base_url, node['href']):
                node['href'] = node['href'].replace(self.base_url, self.get_proxy_root())
            if isinstance(node, bs4.Tag) and node.name not in EXCLUDED_TAGS:
                self._rewrite_string(node)
        return str(soup)

    def get(self, request):
        """
        Send GET request to the base site
        """
        return self.get_response(
            method='GET',
            params=self.params
        )

    def post(self, request):
        """
        Send POST request to the base site
        """
        headers = {}
        if request.META.get('CONTENT_TYPE'):
            headers['Content-type'] = request.META.get('CONTENT_TYPE')
        return self.get_response(
            method='POST',
            body=request.body,
            headers=headers
        )

    def get_response(self, method, params=None, body=None, headers=None):
        """
        Get response from base site
        """
        url = '{}{}'.format(self.base_url, self.url)
        request_session = requests.Session()
        response = request_session.request(
            method=method,
            url=url,
            params=params,
            headers=headers,
            data=body
        )
        proxy_response = HttpResponse(
            response.content,
            status=response.status_code
        )
        return proxy_response
