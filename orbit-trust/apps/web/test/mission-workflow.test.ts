import {test} from 'node:test';
import assert from 'node:assert/strict';
import {Vec3} from '@engine/math';
import {closestApproach,evaluateScenario,buildWorkflow} from '../src/lib/mission-workflow.ts';

test('closest approach stays inside the supplied future horizon',()=>{
  assert.deepEqual(closestApproach(new Vec3(-12,.12,0),new Vec3(.04,0,0)),{seconds:300,distanceKm:.12});
  assert.deepEqual(closestApproach(new Vec3(2,0,0),new Vec3(1,0,0)),{seconds:0,distanceKm:2});
  assert.deepEqual(closestApproach(new Vec3(-100,0,0),new Vec3(1,0,0),10),{seconds:10,distanceKm:90});
  assert.deepEqual(closestApproach(new Vec3(3,4,0),Vec3.zero),{seconds:0,distanceKm:5});
});

test('rotating a relative state preserves time and miss distance',()=>{
  const original=closestApproach(new Vec3(-12,.12,2),new Vec3(.04,0,0));
  const rotated=closestApproach(new Vec3(2,-12,.12),new Vec3(0,.04,0));
  assert.deepEqual(original,rotated);
});

test('invalid inputs cannot emit a reassuring result',()=>{
  for(const bad of [NaN,Infinity,-Infinity])assert.throws(()=>closestApproach(new Vec3(bad,0,0),Vec3.zero));
  assert.throws(()=>closestApproach(Vec3.zero,new Vec3(NaN,0,0)));
  assert.throws(()=>closestApproach(Vec3.zero,Vec3.zero,-1));
});

test('scenarios distinguish review from monitoring without inventing probability or ground damage',()=>{
  const close=evaluateScenario('review'),wide=evaluateScenario('monitor');
  assert.equal(close.review,true);assert.equal(wide.review,false);
  assert.equal(close.stale,true);assert.equal(wide.stale,false);
  assert.equal(close.conditionalLoss,18336000);
  assert.match(close.findings.collision,/Probability withheld/);
  assert.match(wide.findings.collision,/Probability withheld/);
  for(const id of ['review','monitor'] as const){
    const trace=buildWorkflow(id);
    assert.equal(trace.find(e=>e.branch==='terrain')?.state,'withheld');
    assert.match(trace.at(-1)!.detail,/No autonomous maneuver/);
    assert.equal(new Set(trace.map(e=>e.id)).size,trace.length);
  }
});
