"""Representative complete student event; a fixture, not a production default."""
def complete_proposal(**changes):
    fields = dict(club_id='club',title='Future event',summary='Students learn together.',venue='QIU Hall',
                  date='2026-10-22',end_date='2026-10-22',start_time='10:00',end_time='12:00',
                  introduction='A university learning activity.',objectives=['Build student collaboration.','Share practical learning.'],
                  eligibility='QIU students',conclusion='Participants will share their learning.',target_count=30,sdgs=['4'],
                  ict_required=False,logistics_required=False,
                  activities=[{'name':'Discussion','description':'Share project ideas.'}],
                  itinerary=[{'start':'10:00','end':'12:00','agenda':'Discussion and review'}],
                  committee=[{'email':'demo.student@qiu.edu.my','name':'Demo Student','role':'Coordinator','responsibility':'Organise the session'}],revenue=[],expenses=[])
    return dict(fields,**changes)


def drawn_signature():
    """A real visible PNG stroke; never silently injected by the HTTP client."""
    import base64,io
    from PIL import Image,ImageDraw
    canvas=Image.new('RGBA',(240,90),'white')
    ImageDraw.Draw(canvas).line([(10,55),(45,15),(75,70),(120,20),(165,60),(220,25)],fill='black',width=3)
    buffer=io.BytesIO();canvas.save(buffer,format='PNG')
    return 'data:image/png;base64,'+base64.b64encode(buffer.getvalue()).decode()
