import json

merchant_json = json.loads("""{
   "created_at": "2011-11-18T17:07:09Z",
   "description": null,
   "id": "WOQRUJU9OH2HH1",
   "name": "Tom's Delicious Chicken Shop",
   "first_name": "Tom",
   "last_name": "Blomfield",
   "email": "tom@gocardless.com",
   "uri": "https://gocardless.com/api/v1/merchants/WOQRUJU9OH2HH1",
   "balance": "12.00",
   "pending_balance": "0.00",
   "next_payout_date": "2011-11-25T17:07:09Z",
   "next_payout_amount": "12.00",
   "currency": "GBP",
   "sub_resource_uris": {
      "users": "https://gocardless.com/api/v1/merchants/WOQRUJU9OH2HH1/users",
      "bills": "https://gocardless.com/api/v1/merchants/WOQRUJU9OH2HH1/bills",
      "pre_authorizations": "https://gocardless.com/api/v1/merchants/WOQRUJU9OH2HH1/pre_authorizations",
      "subscriptions": "https://gocardless.com/api/v1/merchants/WOQRUJU9OH2HH1/subscriptions"
   }
}
""")

subscription_json = json.loads("""
{
   "amount":"44.0",
   "interval_length":1,
   "interval_unit":"month",
   "created_at":"2011-09-12T13:51:30Z",
   "currency":"GBP",
   "name":"London Gym Membership",
   "description":"Entitles you to use all of the gyms around London",
   "expires_at":null,
   "next_interval_start":"2011-10-12T13:51:30Z",
   "id": "AJKH638A99",
   "merchant_id":"WOQRUJU9OH2HH1",
   "status":"active",
   "user_id":"HJEH638AJD",
   "currency": "GBP",
   "uri":"https://gocardless.com/api/v1/subscriptions/1580",
   "sub_resource_uris":{
      "bills":"https://gocardless.com/api/v1/merchants/WOQRUJU9OH2HH1/bills?source_id=1580"
   }
}
""")

bill_json = json.loads("""
{
   "amount": "10.00",
   "gocardless_fees": "0.10",
   "partner_fees": "0",
   "currency": "GBP",
   "created_at": "2011-11-22T11:59:12Z",
   "description": null,
   "id": "PWSDXRYSCOKA7Z",
   "name": null,
   "status": "pending",
   "merchant_id": "6UFY9IJWGYBTAP",
   "user_id": "BWJ2GP659OXPAU",
   "paid_at": null,
   "source_type": "pre_authorization",
   "source_id": "FAZ6FGSMTCOZUG",
   "payout_id": "XXX",
   "currency": "GBP",
   "uri": "https://gocardless.com/api/v1/bills/PWSDXRYSCOKA7Z"
}""")

preauth_json = json.loads("""
{
   "created_at":"2011-02-18T15:25:58Z",
   "currency":"GBP",
   "name":"Variable Payments For Tennis Court Rental",
   "description":"You will be charged according to your monthly usage of the tennis courts",
   "expires_at":null,
   "id": "1234JKH8KLJ",
   "interval_length":1,
   "interval_unit":"month",
   "merchant_id": "WOQRUJU9OH2HH1",
   "status":"active",
   "remaining_amount": "65.0",
   "next_interval_start": "2012-02-20T00:00:00Z",
   "user_id": "834JUH8KLJ",
   "max_amount": "70.0",
   "currency": "GBP",
   "uri":"https://gocardless.com/api/v1/pre_authorizations/1609",
   "sub_resource_uris":{
      "bills":"https://gocardless.com/api/v1/merchants/WOQRUJU9OH2HH1/bills?source_id=1609"
   }
}""")
