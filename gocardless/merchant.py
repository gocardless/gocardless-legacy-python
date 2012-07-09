class Merchant(object):

    def __init__(self, client, data):
        self.id = data["merchant_id"]
        self.client = client
        self.endpoint = "/merchants/{0}".format(self.id)

    def subscriptions(self):
        """
        Return all the subscriptions for this merchant.
        """
        path = "/merchants/{0}/subscriptions".format(self.id)
        return self.client.subscriptions()

    def subscription(self, subscription_id):
        """
        Return the subscription with id `subscription_id` or `None`
        """
        return self.client.subscription(subscription_id)

    def pre_authorizations(self):
        """
        Return all the pre-authorizations for this merchant
        """
        return self.client.pre_authorizations()

    def pre_authorization(self, pre_authorization_id):
        """
        Return the pre_authorization with `pre_authorization_id` or `None`
        """
        return self.client.pre_authorization(subscription_id)

