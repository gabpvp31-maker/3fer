// Red Rocket: Blender (x,y,z) -> browser (x,z,-y).
// Structural spans preserve the four real walkable door apertures.
export const COLLIDERS = [
 {x:-.425,z:-2,hx:3.575,hz:.15,yaw:0},
 {x:5.30,z:-2,hx:.85,hz:.15,yaw:0},
 {x:13.925,z:-2,hx:1.075,hz:.15,yaw:0},
 {x:2.875,z:-14,hx:6.875,hz:.15,yaw:0},
 {x:13.125,z:-14,hx:1.875,hz:.15,yaw:0},
 {x:-4,z:-8,hx:.15,hz:6,yaw:0},
 {x:15,z:-8,hx:.15,hz:6,yaw:0},
 {x:5.2,z:-4.125,hx:.11,hz:2.125,yaw:0},
 {x:5.2,z:-10.875,hx:.11,hz:3.125,yaw:0},
 {x:4,z:13,hx:1.12,hz:2.9,yaw:-.2},
 {x:-17,z:-9,hx:1.12,hz:2.35,yaw:-1},
 {x:-32,z:0,hx:.15,hz:28,yaw:0},
 {x:32,z:0,hx:.15,hz:28,yaw:0},
 {x:0,z:-28,hx:32,hz:.15,yaw:0},
 {x:0,z:28,hx:32,hz:.15,yaw:0}
];
export function setPropColliders(boxes) {
 COLLIDERS.splice(15, COLLIDERS.length - 15, ...boxes);
 prepared.delete(COLLIDERS);
}
// Cache rotation and conservative broad-phase extents outside the frame loop.
const prepared = new WeakMap();
function prepare(colliders) {
 let result = prepared.get(colliders);
 if (!result) {
  result = colliders.map(box => {
   const c = Math.cos(box.yaw || 0), s = Math.sin(box.yaw || 0);
   return {...box,c,s,ex:Math.abs(c)*box.hx+Math.abs(s)*box.hz,
    ez:Math.abs(s)*box.hx+Math.abs(c)*box.hz};
  });
  prepared.set(colliders,result);
 }
 return result;
}

export function movePlayer(pos, delta, colliders = COLLIDERS, radius = .28) {
 let x = pos.x, z = pos.z;
 const boxes = prepare(colliders);
 // A step shorter than the body radius cannot jump through even a thin wall.
 const steps = Math.max(1, Math.ceil(Math.hypot(delta.x,delta.z)/Math.min(.1,radius*.5)));
 const dx = delta.x/steps, dz = delta.z/steps;
 for (let step=0; step<steps; step++) {
  x += dx; z += dz;
  // Two passes also resolve corners where neighboring bounds overlap.
  for (let pass=0; pass<2; pass++) for (const b of boxes) {
   const ox=x-b.x, oz=z-b.z;
   if(Math.abs(ox)>b.ex+radius || Math.abs(oz)>b.ez+radius) continue;
   let lx=b.c*ox-b.s*oz, lz=b.s*ox+b.c*oz;
   const cx=Math.max(-b.hx,Math.min(b.hx,lx));
   const cz=Math.max(-b.hz,Math.min(b.hz,lz));
   const vx=lx-cx, vz=lz-cz, distance=Math.hypot(vx,vz);
   if(distance>=radius) continue;
   if(distance>1e-9) {
    const push=(radius-distance)/distance;
    lx+=vx*push; lz+=vz*push;
   } else {
    const px=b.hx-Math.abs(lx), pz=b.hz-Math.abs(lz);
    if(px<pz) lx=(lx<0?-1:1)*(b.hx+radius);
    else lz=(lz<0?-1:1)*(b.hz+radius);
   }
   x=b.x+b.c*lx+b.s*lz;
   z=b.z-b.s*lx+b.c*lz;
  }
 }
 return {x,z};
}

export function groundHeight(x,z) {
 if(x>=-4 && x<=15 && z>=-14.2 && z<=-1.8)return .16;
 if(x>=-16.25 && x<=-1.75 && z>=-.8 && z<=1.4)return .18;
 return 0;
}
export function isExit(x,z) { return Math.abs(x)>31.8 || Math.abs(z)>27.8; }
