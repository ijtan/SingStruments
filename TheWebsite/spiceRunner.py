import logging
logger = logging.getLogger()
logger.setLevel(logging.ERROR)

import tensorflow as tf
import tensorflow_hub as hub


import math
import statistics
from scipy.io import wavfile

import music21
from pydub import AudioSegment

#this code is an adaption from the example spice usage provided in https://colab.research.google.com/github/tensorflow/hub/blob/master/examples/colab/spice.ipynb
# it was changed and adapted as required, as to allow it to be used for muscial conversion, and to be u sed on the fly by the server!


print('loading model')
model = hub.load("https://tfhub.dev/google/spice/2")
print('loading model done')


def convert_audio_for_model(user_file, output_file='audio_files/converted_audio_file.wav',EXPECTED_SAMPLE_RATE=16000):
  audio = AudioSegment.from_file(user_file)
  audio = audio.set_frame_rate(EXPECTED_SAMPLE_RATE).set_channels(1)
  audio.export(output_file, format="wav")
  return output_file


def output2hz(pitch_output):
  # Constants taken from https://tfhub.dev/google/spice/2
  PT_OFFSET = 25.58
  PT_SLOPE = 63.07
  FMIN = 10.0;
  BINS_PER_OCTAVE = 12.0;
  cqt_bin = pitch_output * PT_SLOPE + PT_OFFSET;
  return FMIN * 2.0 ** (1.0 * cqt_bin / BINS_PER_OCTAVE)
    
def quantize_predictions(group, ideal_offset):
  # Group values are either 0, or a pitch in Hz.
  non_zero_values = [v for v in group if v != 0]
  zero_values_count = len(group) - len(non_zero_values)

  # Create a rest if 80% is silent, otherwise create a note.
  if zero_values_count > 0.8 * len(group):
    # Interpret as a rest. Count each dropped note as an error, weighted a bit
    # worse than a badly sung note (which would 'cost' 0.5).
    return 0.51 * len(non_zero_values), "Rest"
  else:
    # Interpret as note, estimating as mean of non-rest predictions.
    h = round(
        statistics.mean([
            12 * math.log2(freq / C0) - ideal_offset for freq in non_zero_values
        ]))
    octave = h // 12
    n = h % 12
    note = note_names[n] + str(octave)
    # Quantization error is the total difference from the quantized note.
    error = sum([
        abs(12 * math.log2(freq / C0) - ideal_offset - h)
        for freq in non_zero_values
    ])
    return error, note


def get_quantization_and_error(pitch_outputs_and_rests, predictions_per_eighth,
                               prediction_start_offset, ideal_offset):
  # Apply the start offset - we can just add the offset as rests.
  pitch_outputs_and_rests = [0] * prediction_start_offset + \
                            pitch_outputs_and_rests
  # Collect the predictions for each note (or rest).
  groups = [
      pitch_outputs_and_rests[i:i + predictions_per_eighth]
      for i in range(0, len(pitch_outputs_and_rests), predictions_per_eighth)
  ]

  quantization_error = 0

  notes_and_rests = []
  for group in groups:
    error, note_or_rest = quantize_predictions(group, ideal_offset)
    quantization_error += error
    notes_and_rests.append(note_or_rest)

  return quantization_error, notes_and_rests

def hz2offset(freq):
  # This measures the quantization error for a single note.
  if freq == 0:  # Rests always have zero error.
    return None
  # Quantized note.
  h = round(12 * math.log2(freq / C0))
  return 12 * math.log2(freq / C0) -h




async def getNotes(file_path):
    converted_file = convert_audio_for_model(file_path)
    sample_rate, audio_samples = wavfile.read(converted_file, 'rb')
    
    if(len(audio_samples)<=0):
        print('Empty Audio!')
        return None
    
    MAX_ABS_INT16 = 32768.0
    audio_samples = audio_samples / float(MAX_ABS_INT16)
    global model
    
    # We now feed the audio to the SPICE tf.hub model to obtain pitch and uncertainty outputs as tensors.
    print('running model')
    model_output = model.signatures["serving_default"](tf.constant(audio_samples, tf.float32))
    print('running model done')

    pitch_outputs = model_output["pitch"]
    uncertainty_outputs = model_output["uncertainty"]

    # 'Uncertainty' basically means the inverse of confidence.
    confidence_outputs = 1.0 - uncertainty_outputs
    
    confidence_outputs = list(confidence_outputs)
    pitch_outputs = [ float(x) for x in pitch_outputs]

    indices = range(len (pitch_outputs))\
        
    confident_pitch_outputs = []
    for i, p, c in zip(indices, pitch_outputs, confidence_outputs):
        if  c >= 0.9:
            confident_pitch_outputs.append((i,p))
        else:
            confident_pitch_outputs.append((i,0))
    
    confident_pitch_outputs_x, confident_pitch_outputs_y = zip(*confident_pitch_outputs)
    
    confident_pitch_values_hz = [ output2hz(p) for p in confident_pitch_outputs_y ]
    
    pitch_outputs_and_rests = [
    output2hz(p) if c >= 0.9 else 0
    for i, p, c in zip(indices, pitch_outputs, confidence_outputs)
]
    A4 = 440
    global C0
    global note_names
    C0 = A4 * pow(2, -4.75)
    note_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    
    offsets = [hz2offset(p) for p in pitch_outputs_and_rests if p != 0]
    if(len(offsets)<=0):
        return None
    ideal_offset = statistics.mean(offsets)
    
    best_error = float("inf")
    best_notes_and_rests = None
    best_predictions_per_note = None

    for predictions_per_note in range(20, 65, 1):
        for prediction_start_offset in range(predictions_per_note):

            error, notes_and_rests = get_quantization_and_error(
                pitch_outputs_and_rests, predictions_per_note,
                prediction_start_offset, ideal_offset)

            if error < best_error:      
                best_error = error
                best_notes_and_rests = notes_and_rests
                best_predictions_per_note = predictions_per_note

    # At this point, best_notes_and_rests contains the best quantization.
    # Since we don't need to have rests at the beginning, let's remove these:
    empty = False
    print(len(best_notes_and_rests),' Notes Beofre De-Resting: ',best_notes_and_rests)
    if not best_notes_and_rests or len(best_notes_and_rests)<=0:
            print('Notes Ended before de-resting')
            empty = True
            # return None
    while not empty and best_notes_and_rests[0] == 'Rest':
        best_notes_and_rests = best_notes_and_rests[1:]
        if len(best_notes_and_rests)<=0:
            print('Notes Ended while de-resting')
            empty = True
            break
            # return None
    # Also remove silence at the end.
    if len(best_notes_and_rests)<=0:
            print('Notes Ended while de-resting')
            empty = True
            
    while not empty and best_notes_and_rests[-1] == 'Rest':
        best_notes_and_rests = best_notes_and_rests[:-1]
        if len(best_notes_and_rests)<=0:
            print('Notes Ended while de-resting')
            empty = True
            break
            # return None
        
        
    # Creating the sheet music score.
    sc = music21.stream.Score()
    # Adjust the speed to match the actual singing.
    bpm = 60 * 60 / best_predictions_per_note
    print ('bpm: ', bpm)
    a = music21.tempo.MetronomeMark(number=bpm)
    sc.insert(0,a)

    for snote in best_notes_and_rests:   
        d = 'half'
        if snote == 'Rest':      
            sc.append(music21.note.Rest(type=d))
        else:
            sc.append(music21.note.Note(snote, type=d))
            
    # print(best_notes_and_rests)
    
    return {'predpnote':best_predictions_per_note,'nperrests':best_notes_and_rests,'bpm':bpm}

