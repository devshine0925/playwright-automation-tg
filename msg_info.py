Message(id=357,
         peer_id=PeerUser(user_id=7679124575),
          date=datetime.datetime(2024, 12, 12, 15, 7, 53, tzinfo=datetime.timezone.utc),
          message='OrderID: 202412122207200825800266\nPhone: 0825800266\nDescription: BIG90\nOTP Code: 756720',
            reply_markup=ReplyInlineMarkup(
              rows=[
                      KeyboardButtonRow(
                      buttons=[
                          KeyboardButtonCallback(text='Success', data=b'success', requires_password=False),
                          KeyboardButtonCallback(text='Wrong OTP', data=b'error_otp', requires_password=False),
                          KeyboardButtonCallback(text='Out Money', data=b'no_money', requires_password=False), 
                          KeyboardButtonCallback(text='Already have', data=b'other_data_packages', requires_password=False), 
                          KeyboardButtonCallback(text='Not applicable', data=b'packages_not_found', requires_password=False)]
                          )
                          ]
            ),

        )
