package inq.hpold.injector
{
   import net.wg.gui.battle.components.BattleUIDisplayable;
   import net.wg.gui.battle.views.BaseBattlePage;

   public class BattleDisplayable extends BattleUIDisplayable
   {
      public var battlePage:BaseBattlePage;
      public var componentName:String;

      private var _registered:Boolean = false;

      public function BattleDisplayable()
      {
         super();
      }

      public function initBattle():void
      {
         try
         {
            if (!this.battlePage)
               return;

            if (!this.battlePage.contains(this))
               this.battlePage.addChildAt(this, Math.min(1, this.battlePage.numChildren));

            if (!this.battlePage.isFlashComponentRegisteredS(this.componentName))
            {
               this.battlePage.registerFlashComponent(this, this.componentName);
               this._registered = true;
            }
         }
         catch (e:Error)
         {
            trace("[inq_hpold] BattleDisplayable.initBattle: " + e.message);
         }
      }

      public function finiBattle():void
      {
         try
         {
            if (!this.battlePage)
               return;

            if (this._registered && this.battlePage.isFlashComponentRegisteredS(this.componentName))
               this.battlePage.unregisterFlashComponentS(this.componentName);

            this._registered = false;
            if (this.parent)
               this.parent.removeChild(this);
         }
         catch (e:Error)
         {
            trace("[inq_hpold] BattleDisplayable.finiBattle: " + e.message);
         }
      }

      override protected function onDispose():void
      {
         this.finiBattle();
         this.battlePage = null;
         this.componentName = null;
         super.onDispose();
      }
   }
}
