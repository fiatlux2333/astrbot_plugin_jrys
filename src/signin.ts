import { Context } from 'koishi'
import { Jrys } from "./roll";
import { Config } from '.';
import { } from 'koishi-plugin-monetary'

declare module 'koishi' {
  interface Tables {
    jrys: _UserFortune;
  }
}

export interface _UserFortune {
  id: number    // uid
  name: string  // 昵称
  time: Date  // 最近的签到时间
  exp: number // 总经验
  signCount: number // 签到次数
}

interface TimeGreeting {
  range: [number, number];
  message: string;
}

const timeGreetings: TimeGreeting[] = [
  { range: [ 0,  5], message: '晚安' },
  { range: [ 5,  9], message: '早上好' },
  { range: [ 9, 11], message: '上午好' },
  { range: [11, 14], message: '中午好' },
  { range: [14, 18], message: '下午好' },
  { range: [18, 20], message: '傍晚好' },
  { range: [20, 24], message: '晚上好' },
];

export interface LevelInfo {
  level: number;
  levelExp: number;
  levelName: string;
  levelColor: string;
}

export const defaultLevelInfo = [
  { level: 0, levelExp: 0, levelName: "不知名杂鱼", levelColor: "#838383" },
  { level: 1, levelExp: 500, levelName: "荒野漫步者", levelColor: "#838383" },
  { level: 2, levelExp: 1000, levelName: "拓荒者", levelColor: "#838383" },
  { level: 3, levelExp: 1500, levelName: "冒险家", levelColor: "#838383" },
  { level: 4, levelExp: 2000, levelName: "传说的冒险家", levelColor: "#000000" },
  { level: 5, levelExp: 3000, levelName: "隐秘收藏家", levelColor: "#000000" },
  { level: 6, levelExp: 4000, levelName: "言灵探索者", levelColor: "#42bc05" },
  { level: 7, levelExp: 5000, levelName: "水系魔法师", levelColor: "#42bc05" },
  { level: 8, levelExp: 6000, levelName: "水系魔导师", levelColor: "#42bc05" },
  { level: 9, levelExp: 8000, levelName: "藏书的魔女", levelColor: "#2003da" },
  { level:10, levelExp: 10000, levelName: "人形图书馆", levelColor: "#2003da" },
  { level:11, levelExp: 15000, levelName: "文明归档员", levelColor: "#2003da" },
  { level:12, levelExp: 20000, levelName: "高塔思索者", levelColor: "#03a4da" },
  { level:13, levelExp: 25000, levelName: "未知探索者", levelColor: "#03a4da" },
  { level:14, levelExp: 30000, levelName: "背负真相之人", levelColor: "#9d03da" },
  { level:15, levelExp: 35000, levelName: "守密人", levelColor: "#9d03da" },
  { level:16, levelExp: 40000, levelName: "被缚的倒吊者", levelColor: "#9d03da" },
  { level:17, levelExp: 45000, levelName: "崩毁世界之人", levelColor: "#f10171" },
  { level:18, levelExp: 50000, levelName: "命运眷顾者", levelColor: "#f10171" },
  { level:19, levelExp: 100000, levelName: "文明领航员", levelColor: "#c9b86d" },
  { level:20, levelExp: 1000000, levelName: "天选之人", levelColor: "#ffd000" }
];

export interface FortuneInfo {
  luck: number;
  desc: string;
}

export const defaultFortuneInfo = [
  { luck:  0, desc: '走平坦的路但会摔倒的程度' },
  { luck:  5, desc: '吃泡面会没有调味包的程度' },
  { luck: 15, desc: '上厕所会忘记带纸的程度' },
  { luck: 20, desc: '上学/上班路上会堵车的程度' },
  { luck: 25, desc: '点外卖很晚才会送到的程度' },
  { luck: 30, desc: '点外卖会多给予赠品的程度' },
  { luck: 35, desc: '出门能捡到几枚硬币的程度' },
  { luck: 40, desc: '踩到香蕉皮不会滑倒的程度' },
  { luck: 50, desc: '玩滑梯能流畅滑到底的程度' },
  { luck: 60, desc: '晚上走森林不会迷路的程度' },
  { luck: 70, desc: '打游戏能够轻松过关的程度' },
  { luck: 80, desc: '抽卡能够大成功的程度' },
  { luck: 95, desc: '天选之人' },
];

export const initDatabase = (ctx: Context) => {
  ctx.model.extend("jrys", {
    id: "integer",
    name: "string",
    time: "timestamp",
    exp: "unsigned",
    signCount: "unsigned"
  })
}


// 参数: ctx:Context, config?:Config
export class Signin {
  public ctx:Context;
  public cfg:any;
  constructor( context: Context, config: Config ) {
    this.ctx = context;
    this.cfg = config;
  }

  //             0:签到成功, 1:已签到
  // { "status": 1, "getpoint": signpoint, "signTime": signTime, "allpoint": signpoint, "count": 1 };
  // 参数：session， 返回：json
  async callSignin(uid:number, userid:string, luck:number) {
    const date = new Date();
    const roll = new Jrys();

    const exp = await roll.random(this.cfg.signExp[0], this.cfg.signExp[1], luck);
    const coin = await roll.random(this.cfg.signCoin[0], this.cfg.signCoin[1], luck);

    const userData = await this.ctx.database.get('jrys', {id: uid});
    
    if( userData.length === 0) { // No UserData -> Create new one
      let accCount = 1;
      let accExp = exp;
      
      this.ctx.database.create('jrys', {
        id:uid,
        name:userid,
        time: date,
        exp: accExp,
        signCount: accCount
      });
      this.ctx.monetary.gain(uid, coin, this.cfg.currency);

      return { status: 0, getExp: exp, allExp: accExp, getCoin: coin, signTime: date, count: accCount };
    }

    if( userData[0].time.getDate() === date.getDate() ) { // Already Signin today
      return { status: 1 }
    } else { // Update User Data
      let accExp = userData[0].exp + exp;
      let accCount = userData[0].signCount+1;
      this.ctx.database.set('jrys', {id: uid}, {
        name: userid,
        time: date,
        exp: accExp,
        signCount: accCount
      })
      this.ctx.monetary.gain(uid, coin, this.cfg.currency);

      return { status: 0, getExp: exp, allExp: accExp, getCoin: coin, signTime: date, count: accCount };
    }
  }

  getLevelInfo(exp: number, info: LevelInfo[]) {
    let index = 0;
    for (let i = 0; i < info.length; i++) {
      if( exp>=info[i].levelExp ) {index++} else {break};
    }
    let nExp:number | string;
    if(index >= info.length) { nExp = '???' } else { nExp = info[index].levelExp }
    index--;
    return {
      levelInfo: info[index],
      nextExp: nExp
    };
  }

  getFortuneInfo(luck: number, info: FortuneInfo[]): string {
    let index = 0;
    for (let i = 0; i < info.length; i++) {
      if( luck>=info[i].luck ) {index++} else {break};
    }; index--;

    return info[index].desc;
  }

  getGreeting(hour: number): string {
    const greeting = timeGreetings.find((timeGreeting) =>
      hour >= timeGreeting.range[0] && hour < timeGreeting.range[1]
    );

    return greeting ? greeting.message : '你好';
  }

}
