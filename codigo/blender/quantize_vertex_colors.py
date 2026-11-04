"""Store normalized glTF vertex colours as bytes, matching the authoring mesh.

Only dedicated, non-interleaved colour buffer views are rewritten. Positions,
normals, UVs and triangle indices are copied without changes.
"""
import json,struct
from pathlib import Path

def quantize_vertex_colors(path):
 path=Path(path);data=path.read_bytes()
 magic,version,size=struct.unpack_from('<III',data)
 assert (magic,version,size)==(0x46546c67,2,len(data))
 length,kind=struct.unpack_from('<II',data,12);assert kind==0x4e4f534a
 document=json.loads(data[20:20+length])
 offset=20+length;binary_size,binary_kind=struct.unpack_from('<II',data,offset)
 assert binary_kind==0x004e4942
 binary=data[offset+8:offset+8+binary_size]
 colors={p['attributes']['COLOR_0'] for mesh in document['meshes'] for p in mesh['primitives'] if 'COLOR_0' in p['attributes']}
 replacements={}
 for index in colors:
  accessor=document['accessors'][index]
  if accessor['componentType']!=5123:continue
  view_index=accessor['bufferView'];view=document['bufferViews'][view_index]
  assert accessor['type']=='VEC4' and accessor.get('normalized') is True
  assert not view.get('byteStride') and not accessor.get('byteOffset')
  assert view['byteLength']==accessor['count']*8
  assert sum(a.get('bufferView')==view_index for a in document['accessors'])==1
  start=view.get('byteOffset',0);raw=binary[start:start+view['byteLength']]
  values=struct.unpack('<'+'H'*(len(raw)//2),raw)
  replacements[view_index]=bytes(round(value/257) for value in values)
  accessor['componentType']=5121
 output=bytearray()
 for index,view in enumerate(document['bufferViews']):
  output.extend(b'\0'*(-len(output)%4))
  start=view.get('byteOffset',0)
  raw=replacements.get(index,binary[start:start+view['byteLength']])
  view['byteOffset']=len(output);view['byteLength']=len(raw);output.extend(raw)
 output.extend(b'\0'*(-len(output)%4));document['buffers'][0]['byteLength']=len(output)
 header=json.dumps(document,separators=(',',':')).encode();header+=b' '*(-len(header)%4)
 result=struct.pack('<III',magic,2,12+8+len(header)+8+len(output))+struct.pack('<II',len(header),0x4e4f534a)+header+struct.pack('<II',len(output),0x004e4942)+output
 path.write_bytes(result)
 return {'beforeBytes':len(data),'afterBytes':len(result),'colorAccessors':len(replacements),'maximumColorError':.5/255,'triangles':sum(document['accessors'][p['indices']]['count']//3 for m in document['meshes'] for p in m['primitives'])}
