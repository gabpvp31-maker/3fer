import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {COLLIDERS, movePlayer, groundHeight, setPropColliders} from '../red-rocket/src/physics.mjs';

const path = new URL('../red-rocket/assets/prop-colliders.json', import.meta.url);
if(fs.existsSync(path))setPropColliders(JSON.parse(fs.readFileSync(path)));
const near=(a,b)=>assert.ok(Math.abs(a-b)<.001, `${a} != ${b}`);
function traverse(route){
 let p={x:route[0][0],z:route[0][1]};
 for(const [x,z] of route.slice(1)){
  const dx=x-p.x,dz=z-p.z,n=Math.ceil(Math.hypot(dx,dz)/.04);
  for(let i=0;i<n;i++)p=movePlayer(p,{x:dx/n,z:dz/n});
  near(p.x,x);near(p.z,z);
 }
 return p;
}
test('road arrival reaches garage destination through actual bay',()=>{
 traverse([[-10,24],[-7,14],[-1,6],[4,0],[9.5,0],[9.5,-4],[9.5,-10]]);
});
test('personnel entrance and interior connection stay open in both directions',()=>{
 const route=[[4,0],[3.8,-3],[3.8,-7],[6.2,-7],[9.5,-7]];
 traverse(route);traverse([...route].reverse());
});
test('rear door opens onto rear apron',()=>traverse([[12,-10],[12,-13.3],[10.5,-13.3],[10.5,-16]]));
test('solid walls and glazed windows block walking',()=>{
 assert.ok(movePlayer({x:0,z:0},{x:0,z:-4}).z>=-1.571);
 assert.ok(movePlayer({x:-6,z:-7},{x:5,z:0}).x<=-4.429);
});
test('foreground wreck stops a player crossing its body',()=>{
 const result=movePlayer({x:0,z:13},{x:7,z:0});
 assert.ok(result.x<3);
});
test('slabs have actual walkable heights and scene boundaries stop movement',()=>{
 near(groundHeight(9.5,-8),.16);near(groundHeight(-9,0),.18);near(groundHeight(-10,24),0);
 assert.ok(movePlayer({x:30,z:0},{x:4,z:0}).x<=31.571);
});
test('generated prop collisions remain finite and within authored map bounds',()=>{
 for(const box of COLLIDERS){
  for(const key of ['x','z','hx','hz'])assert.ok(Number.isFinite(box[key]));
  assert.ok(box.hx>0&&box.hz>0&&box.hx<=33&&box.hz<=29);assert.ok(Math.abs(box.x)<34&&Math.abs(box.z)<30);
 }
});
