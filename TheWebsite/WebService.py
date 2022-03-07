from fastapi import FastAPI, Request, File, UploadFile, Form
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
# from time import sleep
import asyncio

from music21.environment import keys 
import spiceRunner
import instrumentalMidi
import datetime

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

current_files = {}
aud_dir = 'audio_files'
win_tim_path = '..\\win-timidity\\timidity.exe'

xmls = None


@app.get("/", response_class=HTMLResponse)
async def read_item(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})


@app.get("/info", response_class=HTMLResponse)
async def read_item(request: Request):
    return templates.TemplateResponse("info.html", {"request": request})


@app.post("/upload_audio_file/")
async def create_upload_file(item_id: str = Form(...), file: UploadFile = File(...)):
    
    print('Got notes request for id',item_id)
    filename = file.filename
    contents = await file.read()
    filename = filename.replace(':', '-').replace('.', '_')
    old_dir = os.path.join(aud_dir, filename+'.wav')

    # old_dir = aud_dir+'/'+filename+'.wav'
    # new_dir = aud_dir+'/'+filename+'.wav'

    with open(old_dir, 'wb') as f:
        f.write(contents)
        

        
    notes = await spiceRunner.getNotes(old_dir)
    if notes is None:
        return {"id": item_id, "directory": old_dir, "notes": [], 'bpm': 0}
        
    best_predictions_per_note = notes['predpnote']
    best_notes_and_rests      = notes['nperrests']
    bpm = notes['bpm']
    
    
    print(f'got notes:',notes)
    current_files[item_id] = {'new_path': old_dir+'.wav', 'notes': notes,'bpm':bpm}
    # os.remove(old_dir)
    return {"id": item_id, "directory": old_dir, "notes": best_notes_and_rests}

isProcessing = False

@app.get("/get_xml/")
async def get_xml(id: str):
    global current_files
    global isProcessing
    global xmls
    count=0;
    print(list(current_files.keys()))
    # print(f'{id not in current_files} {"xml" not in current_files[id]} {isProcessing} {count<=100}')
    # while id not in current_files and "xml" not in current_files[id] and count<=100:
    #     print(f'{id not in current_files} {"xml" not in current_files[id]} {isProcessing} {count<=100}')
    #     print('Waiting for model...')
    #     count+=1
    #     sleep(0.1)
    # if id not in current_files and "xml" not in current_files[id]:
    #     print(f'{id} not found in files!')
    #     print(list(current_files.keys()))
    #     return {'Error':f'Item id {id} not defined!'}
    print(f'{ xmls is None} {count<=100}')
    while xmls is None and count<=100:
        print(f'{ xmls is None} {count<=100}')
        print('Waiting...')
        count+=1
        await asyncio.sleep(0.1)
    print(f'{ xmls is None} {count<=100}')
        
        
    
    if id not in current_files:
        print(f'{id} not found in files!')
        print(list(current_files.keys()))
        return {'Error':f'Item id {id} not defined!'}
    print(f'xml request {id}')
    
    print(f'got id {id}')
    old_xml = xmls
    # current_files[id]['xml'] = None 
    # current_files = {}
    xmls = None
    return {'xml':old_xml}#do we need to re-get the audio file?



@app.get("/get_audio_file/")
async def get_audio_file(item_id: str, instrument:str): #do we need to re-get the audio file?
    global current_files
    global xmls
    global isProcessing
    instrument = instrument.lower()
    if instrument == "":
        return {'Error':'Instrument not specified'}
    print(f'Got conversion request for id {item_id} into {instrument}')
    file_path = ""
    
    
    
    if item_id not in current_files:
        return {'Error':'Item id not defined!'}#
    #
    
    
    
    old_path = current_files[item_id]['new_path'].split('.')[0]+'.mid'
    notes = current_files[item_id]['notes']
    if notes == []:
        return ''
    isProcessing = True
    pred_p_note = notes['predpnote']
    note_per_rests = notes['nperrests']
    bpm = notes['bpm']
    
    mid_path = old_path
    # mid_path = os.path.join(aud_dir, old_path)
    mid_path,xml = instrumentalMidi.instrumentConversion(pred_p_note,note_per_rests,instrument,mid_path)
    print(f'got xml')
    if xml is None:
        print('XML IS NONE!!!!!!!!!')
        xml =''
    xmls = xml

    
    
    wav_dir = mid_path[:-4]+'.wav'
    if os.name == 'nt':
        os.system(f'{win_tim_path} {mid_path} -Ow -o {wav_dir} -T {bpm}')
    else:
        os.system(f'timidity {mid_path} -Ow -o {wav_dir} -T {bpm}')
    
    # adir = os.path.join(wav_dir, wav_dir)
    isProcessing = False
    return FileResponse(wav_dir)
    # return {"id":item_id,"audio":FileResponse(file_path)}# and the new audio file
    
    
# @app.get('/getMidiFile')
# def getMidiFileTest():
    
#     # fs = FluidSynth()
#     # FluidSynth().play_midi('input.mid')
    
#     mdir = os.path.join(aud_dir, 'input.mid')
#     adir = mdir[:-4]+'.wav'
    
#     os.system(f'timidity {mdir} -Ow -o {adir}')
#     print('re:',adir)
#     return FileResponse(adir)





print("\n\nApp started Successfully!\n\n")