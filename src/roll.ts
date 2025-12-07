// 获取每日运势值，随机4个黄历对象

export class Jrys {
  constructor() {}

  seededRandom(seed: number): number {
    const x = Math.sin(seed) * 10000;
    return x - Math.floor(x);
  }

  // 获取随机运势，范围默认0-100，同一天中运势相同
  async getFortune(uid: number, maxRange: number = 100 ): Promise<number> {
    // get today time seed
    const etime = new Date().setHours(0,0,0,0);
    let userId = Number(uid);

    const todaySeed = (userId * etime) % 1000000001;
    const todayJrys = Math.floor(this.seededRandom(todaySeed) * maxRange);

    return todayJrys;
  }

  // 抽取四个宜不宜
  async getRandomObjects(jsonObject: Array<any>, uid: number): Promise<Array<any>> {
    if (!Array.isArray(jsonObject) || jsonObject.length < 4) {
      throw new Error("输入必须是一个包含至少四个对象的数组");
    }

    const seed = await this.getFortune(uid);
    const randomIndexes: Set<number> = new Set();

    let counter = 0;
    while (randomIndexes.size < 4) {
      const randomIndex = Math.floor(this.seededRandom(seed + counter) * jsonObject.length);
      randomIndexes.add(randomIndex);
      counter++;
    }

    return Array.from(randomIndexes).map(index => jsonObject[index]);
  }

  async random(min: number, max: number, luck: number = 50): Promise<number>  {
    let rmin = min;
    let rmax = max;
    if(max < min) {
      rmin = max;
      rmax = min;
    }

    const mean = luck/100;
    const std = 0.12;

    // Generate Guass number through Box-Muller methord
    let a:number, b:number;
    do {
      a = Math.random();
      b = Math.random();
    } while(a==0.0 || b==0.0)
    let rand = Math.cos(2*Math.PI*a)*Math.sqrt(-2*Math.log(b));
    rand = rand*std+mean;

    // Fold
    if(rand > 1) {
      rand = 2-rand;
    } else if(rand < 0) {
      rand = -rand;
    }

    // Keep in range
    if(rand > 1) {
      rand = 1
    } else if(rand < 0) {
      rand = 0;
    }

    return Math.round(rand*(rmax-rmin)+rmin);
  }
}
