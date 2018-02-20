"""
Implements means of exchanging user ID token with temporary access and secret key.
"""

from ..exceptions import *
from ..interfaces.providers import *

import requests
import xml.etree.ElementTree as ET


class Authorize(IProvider):

    action = "AssumeRoleWithWebIdentity"
    version = "2011-06-15"
    namespace = '{https://sts.amazonaws.com/doc/2011-06-15/}'

    def __init__(self):
        pass

    def __parse_error(self, response):
        """
        Parses the AWS STS xml-based error response, and throws appropriate exception.

        :type  response: string
        :param response: error xml

        :rtype : CloudAuthzBaseException (or any of its derived classes)
        :return: a CloudAuthz exception w.r.t. AWS STS error code.
        """
        root = ET.fromstring(response)
        error = root.find('{}Error'.format(self.namespace))
        code = error.find('{}Code'.format(self.namespace)).text
        message = error.find('{}Message'.format(self.namespace)).text
        if code == 'ExpiredTokenException':
            return ExpiredTokenException(message)
        else:
            return CloudAuthzBaseException

    def get_credentials(self, identity_token, role_arn, duration, role_session_name):
        """
        Assumes an AWS Role and returns credentials accordingly.

        :type  identity_token: string representing a JSON Web Token (JWT)
        :param identity_token: OpenID Connect ID token generated by an
        OpenID Connect Identity Provider (e.g., Google).

        :type  role_arn: string
        :param role_arn: an Amazon Resource Name (ARN) of a role to be assumed.

        :type  duration: integer
        :param duration: session duration in seconds; credentials will expire
        after this period. Valid values range from 900 seconds to 3600 seconds.

        :type  role_session_name: string
        :param role_session_name: a name assigned to the session, consisting of
        lower and upper-case letters with no space.

        :rtype : dict
        :return: a dictionary containing credentials to access the resources
        available to the assumed role. Credentials are:
        - Access Key ID
        - Secret Access Key
        - Session Token
        """
        url = "https://sts.amazonaws.com/?" \
              "DurationSeconds={}&" \
              "Action={}&Version={}&" \
              "RoleSessionName={}&" \
              "RoleArn={}&" \
              "WebIdentityToken={}"\
            .format(duration, self.action, self.version, role_session_name,role_arn, identity_token)
        response = requests.get(url)

        if response.ok:
            root = ET.fromstring(response.content)
            rtv = {}
            role_assume_result = root.find('{}AssumeRoleWithWebIdentityResult'.format(self.namespace))
            credentials = role_assume_result.find('{}Credentials'.format(self.namespace))
            for attribute in credentials:
                rtv[attribute.tag.replace(self.namespace, '')] = attribute.text
            return rtv
        else:
            raise self.__parse_error(response.content)
