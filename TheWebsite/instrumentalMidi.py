import music21
from music21 import converter, instrument


instrumentClass = {
    "harmonica": instrument.Harmonica(),
    "trumpet": instrument.Trumpet(),
    "electric guitar": instrument.ElectricGuitar(),
    "piano": instrument.Piano(),
    "saxophone": instrument.AltoSaxophone(),
    "violin": instrument.Violin()
}


def instrumentConversion(best_predictions_per_note, best_notes_and_rests, instrument_choice, output_file):

    sc = music21.stream.Score()
    # Adjust the speed to match the actual singing.
    bpm = 60 * 60 / best_predictions_per_note
    print ('bpm: ', bpm)
    a = music21.tempo.MetronomeMark(number=bpm)
    sc.insert(0, a)

    for snote in best_notes_and_rests:
        d = 'half'
        if snote == 'Rest':
            sc.append(music21.note.Rest(type=d))
        else:
            sc.append(music21.note.Note(snote, type=d))

    sc.write('midi', 'inputs.mid')
    xml = open(sc.write('musicxml')).read()

    s = converter.parse('inputs.mid')

    if instrument_choice not in instrumentClass:
        return 'Error, instrument Class not found!',''
    chosen_instrument = instrumentClass[instrument_choice]

    for el in s.recurse():
        if 'Instrument' in el.classes:  # or 'Piano'
            el.activeSite.replace(el, chosen_instrument)

    # FileName = instrument_choice+".mid"
    s.write('midi', output_file)
    return output_file,xml
